from celery import shared_task
import pandas as pd
import os
import ast
import requests
import json
import random
import logging
import wandb
import time
import yaml
import uuid
import subprocess
from django.db.models import Q, Count
from boostedchatScrapper.spiders.instagram import InstagramSpider
from boostedchatScrapper.spiders.helpers.instagram_login_helper import login_user
from django.utils import timezone
from api.instagram.models import InstagramUser,Account, Message, OutSourced, StatusCheck, Thread, UnwantedAccount, OutreachTime
from api.scout.models import Scout
from api.instagram.utils import initialize_hikerapi_client
from django_tenants.utils import schema_context
from boostedchatScrapper.spiders.constants import STYLISTS_WORDS,STYLISTS_NEGATIVE_WORDS
import datetime
import json
import logging
import time
import random
import backoff
import requests
from datetime import datetime, timedelta

from celery import shared_task
from lunyamwi.model_setup import setup_agent_workflow
from django.conf import settings
from api.dialogflow.helpers.notify_click_up import notify_click_up_tech_notifications, create_click_up_task
from django_celery_beat.models import PeriodicTask
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from api.sales_rep.models import SalesRep
from api.dialogflow.helpers.get_prompt_responses import get_gpt_response

from api.instagram.utils import get_account,assign_salesrep
from api.instagram.utils import initialize_hikerapi_client
from api.instagram.constants import STYLISTS_WORDS
from api.instagram.prequalifying import prequalifying_automatically
from api.workflow.models import WorkflowModel, DagModel, SimpleHttpOperatorModel, AirflowCreds, ContentType, HttpOperatorConnectionModel, Endpoint, CustomFieldValue, CustomField   
# from tabulate import tabulate # for print_logs
from urllib.parse import urlparse
from api.sales_rep.helpers.task_allocation import no_consecutives, no_more_than_x,get_moving_average
from api.workflow.utils import flatten_dict,remove_timestamp,merge_lists_by_timestamp,flatten_dict_list
from api.workflow.dag_generator import generate_dag
from api.sales_rep.models import SalesRep, Influencer, LeadAssignmentHistory
from django.db.models import Q
from django.conf import settings
from django_tenants.utils import schema_context

import socket
# test
false = False


db_url = f"postgresql://{os.getenv('POSTGRES_USERNAME')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DBNAME')}"
load_tables = True



def sales_rep_is_logged_in(account, salesrep):
    igname =  account_has_sales_rep(account)
    data = {
        "igname": igname
    }
    json_data = json.dumps(data)
    response = requests.post(settings.MQTT_BASE_URL + "/accounts/isloggedin", data=json_data, headers={"Content-Type": "application/json"})
    if response.status_code == 200:
        account_list = None
        try:
            account_list = response.json()
        except ValueError:
            outreachErrorLogger(account, salesrep, "Wrong response data. Not JSON", 422, "WARNING", "MQTT", False)
            return False
            # handle error and thoww
        
        if igname in account_list:
            print(f"print is returning....{account_list[igname]}")
            return account_list[igname]
        else:
            outreachErrorLogger(account, salesrep, "Wrong Json data", 422, "WARNING", "MQTT", False)
        return False
    return False

@schema_context(os.getenv("SCHEMA_NAME"))
def sales_rep_is_available(account):
    salesrep = account.salesrep_set.filter()
    if salesrep.exists():
        return salesrep.latest('created_at').available
    else:
        srep = SalesRep.objects.get(ig_username="barbersince98")
        srep.instagram.add(account)
        return srep.available

@schema_context(os.getenv("SCHEMA_NAME"))
def account_has_sales_rep(account):
    salesrep = account.salesrep_set.first()
    if salesrep is not None:
        return salesrep.ig_username
    else:
        srep = SalesRep.objects.get(ig_username="barbersince98")
        srep.instagram.add(account)
        return srep.ig_username

    
def outreachErrorLogger(account, sales_rep, error_message, err_code, log_level, error_type, repeat = False):
    #save
    # react
    if log_level == "WARNING":
        pass
    else: # not action to be taken
        raise Exception(error_message) # ERROR will break execution after rescheduling if repeat is True

def handleMqTTErrors(account, sales_rep, status_code, status_message, numTries, repeat):
    repeatLocal = False # to repeat within calling func without resheduling new. Valid only for authcodes
    error_type = "unknown"  # Default error type

    auth_codes = [401, 403]
    our_errors = [400]

    if status_code in auth_codes:
        error_type = "Sales Rep"
    if status_code in [500]:
        error_type = "Instagram"
    if status_code in our_errors:
        error_type = "MQTT"
    ## 400, others

    log_level = "WARNING" # default
    if status_code in auth_codes and numTries == 1: # first trial of login, enable repeat
        if logout_and_login(account, sales_rep):
            repeatLocal = True
    if status_code in auth_codes and numTries > 1:
        log_level = "ERROR"

    if status_code in auth_codes:
        repeat = False # it will repeat locally using repeatLocal
    try:
        outreachErrorLogger(account, sales_rep, status_message, status_code, log_level, error_type, repeat)
    except Exception as e:
        pass

    # if status_code not in auth_codes and repeat: # by default repeat is true. But we may set it to false for single action trials
    #     reschedule_last_enabled(sales_rep.ig_username)  #### this should be handled by outreachErrorLogger
    
    return repeatLocal
    

def logout(igname):
    data = {
        "igname": igname
    }
    # Convert the data to JSON format
    json_data = json.dumps(data)
    response = requests.post(settings.MQTT_BASE_URL + "/accounts/logout", data=json_data, headers={"Content-Type": "application/json"})
    # Check the response
    if response.status_code == 200:
        print("Logout successful")
    else:
        print("Logout failed:", response.text)

def login(account, salesrep):
    igname = salesrep.ig_username
    data = {
        "igname": igname
    }
    # Convert the data to JSON format
    json_data = json.dumps(data)
    response = requests.post(settings.MQTT_BASE_URL + "/accounts/login", data=json_data, headers={"Content-Type": "application/json"})
    # Check the response
    if response.status_code == 200:
        print("login successful")
        return True
    else:
        print("login failed:", response.text, response.status_code)
        outreachErrorLogger(account, salesrep, response.text, response.status_code, "ERROR", "Account")
        
        #  check: we ill need to handle challenges here
        return False


def logout_and_login(account, salesrep):
    igname = salesrep.ig_username
    logout(igname)
    if not login(account, salesrep):
        return False
    time.sleep(20)
    return True
    # handle response from these...
    # Error handler for this one
def isMQTTUP():
    parsed_url = urlparse(settings.MQTT_BASE_URL)
    print(settings.MQTT_BASE_URL)
    # Get the host and port from the parsed URL
    host = parsed_url.hostname
    scheme = parsed_url.scheme

    # Map the scheme to the default port
    default_ports = {'http': 80, 'https': 443}
    port = parsed_url.port or default_ports.get(scheme.lower(), None)

    print(f"Host: {host}")
    print(f"Port: {port}")
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)  # 5 seconds timeout
        s.connect((host, port))
        
        # Connection successful
        print(f"Microservice running on port {port} is available.")
        return True
        
    except Exception as e:
        # Connection failed or timed out
        print(f"Microservice running on port {port} is not available: {e}")
        return False
        
    finally:
        # Close the socket
        s.close()
def user_exists_in_IG(account, salesrep):
    data = {"username_from": salesrep.ig_username, "username_to": account.igname}
    response = requests.post(settings.MQTT_BASE_URL + "/checkIfUserExists", data=json.dumps(data))
    if response.status_code == 200:
        return True
    elif response.status_code == 404:
        return False
    else:
        raise Exception(f"Unexpected status code: {response.status_code}")

def delete_first_compliment_task(account):
    try:
        PeriodicTask.objects.get(name=f"SendFirstCompliment-{account.igname}").delete()
    except Exception as error:
        logging.warning(error)


def like_and_comment(media_id, media_comment, salesrep, account):
    like_comment = False
    datasets = []
    dataset = {
        "mediaId": media_id,
        "username_from": salesrep.ig_username
    }
    datasets.append(dataset)
    response =  requests.post(settings.MQTT_BASE_URL + "/like", data=json.dumps(dataset),headers={"Content-Type": "application/json"})
    datasets = []
    if response.status_code == 200:
        time.sleep(105) # we break for 1 minute 45 seconds and then comment
        dataset = {
            "mediaId": media_id,
            "comment": media_comment,
            "username_from": salesrep.ig_username
        }
        datasets.append(dataset)
        print(f"************* {account.igname} media has been liked ****************" )
        # response =  requests.post(settings.MQTT_BASE_URL + "/comment", data=json.dumps(datasets))
        # if response.status_code == 200:
        #     like_comment = True
            

        #     print(f"************* {account.igname} media has been liked and commented ****************" )
        # else:
        #     outreachErrorLogger(account, salesrep, response.text, response.status_code, "WARNING", "Commenting", False) # reshedule_next
        
    else:
        outreachErrorLogger(account, salesrep, response.text, response.status_code, "WARNING", "Liking", False) # reshedule_next
        print(f"************* {account.igname} media has not been liked and commented ****************" )
    return like_comment


@shared_task()
def run_scheduler(target_time,username,message):
    """
    A custom scheduler to execute a task at the specified target time.
    
    :param target_time: The datetime object specifying when to run the task.
    """
    print(f"Scheduler started. Current time: {timezone.now()}, Target time: {target_time}")
    
    while True:
        now = timezone.now()
        if now >= target_time:
            send_first_compliment(list(username),message)
            break  # Exit the loop after running the task
        time.sleep(1)  # Sleep for 1 second to avoid busy-waiting

@shared_task()
@schema_context(os.getenv("SCHEMA_NAME"))
def delete_accounts(duplicate_igname_list):
    for igname in duplicate_igname_list:
        accounts = Account.objects.filter(igname=igname).order_by('-created_at')
        accounts_to_delete = accounts[1:]  # Keep the latest one, delete the rest
        delete_count = Account.objects.filter(id__in=[acc.id for acc in accounts_to_delete]).delete()
        print(f"Deleted {delete_count} duplicate(s) for igname: {igname}")


@shared_task()
@schema_context(os.getenv("SCHEMA_NAME"))
def send_first_compliment(username, message, repeat=True):
    """
    Send the first compliment to a user.
    :param username: The Instagram username of the user to send the compliment to.
    :param message: The message to send as a compliment.
    :param repeat: Whether to repeat the task if it fails.
    :return: None
    """
    numTries = 0
    print("Searching for:::>>>>>> ", username)
    account = get_account(username)

    if account is None:
        err_str = f"{username} account does not exist"
        outreachErrorLogger(None, None, err_str, 404, "ERROR", "Lead", True) # reshedule_next
        # raise Exception(err_str)
        
    print("Found Account:::>>>>>> ", account)
    thread_obj = None
    
    account.status_param = 'Prequalified'
    # account.outreach_time = target_time
    account.save()

        
    # check that account has sales_rep
    check_value = account_has_sales_rep(account)

    if not check_value:
        err_str = f"{username} has no sales rep assigned"
        outreachErrorLogger(account, None, err_str, 404, "ERROR", "Sales Rep", True) # reshedule_next
        outreachErrorLogger(err_str)
        raise Exception(err_str)

    
    account_sales_rep_ig_name = check_value
    check_value = sales_rep_is_available(account)
    if not check_value:
        err_str = f"{account_sales_rep_ig_name} sales rep set for {username} is not available"
        outreachErrorLogger(account, None, err_str, 422, "ERROR", "Sales Rep", False) # Nothing to be done. No action on our part can make it available
    
    salesrep = account.salesrep_set.first()
    if not isMQTTUP():
        outreachErrorLogger(account, salesrep, "MQTT service unavailable. Not handled", 503, "ERROR", "MQTT", False) # Nothinig to be done. No action on our part can bring it up
    
    
    # raise Exception("There is something wrong with mqt----t")
    outsourced_data = OutSourced.objects.filter(account=account)
    results = None
    try:
        if isinstance(outsourced_data.last().results, str):
            results = eval(outsourced_data.last().results)
        else:
            results = outsourced_data.last().results
    except:
        results = {"media_id": "", "media_comment": ""}
    print(f"results================{results}")
    print(f"results================MMM")
    print(f"results================{message}")
    first_message = None
    try:
        first_message = get_gpt_response(account,message)
    except Exception as err:
        logging.warning(f"error: {err}")

    media_id = results.get("media_id", "")
    data = {"username_from":salesrep.ig_username,"message": first_message, "username_to": account.igname, "mediaId": media_id}
    

    # like and comment
    is_like_and_comment = like_and_comment(media_id=media_id, media_comment=results.get("media_comment", ""),
                     salesrep=salesrep, account=account)
    if is_like_and_comment:
        time.sleep(60) # we break for 1 minute then send message
        print("successfully liked and commented")
    

    print(f"data=============={data}")
    print(f"data=============={json.dumps(data)}")
    
    def send(numTries = 0):
        def should_retry_on_response(response):
            # Retry on HTTP 401 or 403
            return response is not None and response.status_code in [401, 403]

        @backoff.on_predicate(
            backoff.constant,
            predicate=should_retry_on_response,
            interval=90,  # 90 seconds delay between retries
            max_tries=3,
            jitter=None  # no jitter for exact timing
        )
        def send_request():
            # try:
            print(f"Sending message attempt for username: {username}")
            response = requests.post(
                settings.MQTT_BASE_URL + "/send-first-media-message",
                data=json.dumps(data),
                headers={"Content-Type": "application/json"}
            )
            print(f"Response status code: {response.status_code}")

            if response.status_code in [401, 403]:
                # Refresh login session on auth errors
                notify_click_up_tech_notifications(
                    comment_text=f"Received {response.status_code} - relogin attempt for {salesrep.ig_username}, and I shall retry doing this 3 times with a 90 seconds interval",
                    notify_all=True
                )
                restart_payload = {"container_id": "boostedchat-site-mqtt-1"}  # restart the mqtt container
                restart_mqtt = requests.post(f"{os.getenv('API_URL')}/serviceManager/restart-container/",data=restart_payload)
                        
                if restart_mqtt.status_code == 200:
                    notify_click_up_tech_notifications(
                        comment_text=f"Received {restart_mqtt.status_code} - after trying to relogin the following salesrep {salesrep.ig_username} and now we can proceed on to sending the message",
                        notify_all=True
                    )
                    time.sleep(90)  # Wait for 90 seconds before retrying

            elif response.status_code in [500, 502, 503, 504, 405, 400]:
                notify_click_up_tech_notifications(
                        comment_text=f"Received the following error:{response.text} - {username}, and I shall not retry to login for this case, instead I shall just proceed to the next individual I shall do a maximum of 5 accounts in order to save on gpt credits",
                        notify_all=True
                )
                message = "" # reset message to avoid sending the same message again
                max_retries = 5  # Setting a maximum retry limit in order to save on credits
                retries = 0
                while retries < max_retries:
                    try:
                        next_account = get_account()
                        send_first_compliment(next_account, message)
                        break  # Exit the loop if successful
                    except Exception as inner_error:
                        retries += 1
                        notify_click_up_tech_notifications(comment_text=f"Retry: {retries}/{max_retries} failed: {inner_error} account: {username}",notify_all=True)
                        if retries >= max_retries:
                            notify_click_up_tech_notifications(
                                comment_text=f"Max retries reached for {username}. Skipping to the next individual.",
                                notify_all=True
                            )
                            break
            elif response.status_code == 522:
                notify_click_up_tech_notifications(
                        comment_text=f"Received the following error:{response.text} - {username}, waiting for 10 minutes before login retry",
                        notify_all=True
                )
                time.sleep(600)  # Wait for 30 minutes before retrying
                restart_payload = {"container_id": "boostedchat-site-mqtt-1"}  # restart the mqtt container
                restart_mqtt = requests.post(f"{os.getenv('API_URL')}/serviceManager/restart-container/",data=restart_payload)
                        
                if restart_mqtt.status_code == 200:
                    notify_click_up_tech_notifications(
                        comment_text=f"Received {restart_mqtt.status_code} - after trying to relogin the following salesrep {salesrep.ig_username} and now we can proceed on to sending the message",
                        notify_all=True
                    )
            return response
            

        # Execute send with retries handled by backoff decorator
        response = send_request()

        # numTries += 1
        # try:
        #     # TODO: authenticate this mqtt request
        #     response = requests.post(settings.MQTT_BASE_URL + "/send-first-media-message", data=json.dumps(data),headers={"Content-Type": "application/json"})
        #     print("coming in as data")
        # except Exception as error:
        #     try:
        #         # TODO: authenticate this mqtt request
        #         response = requests.post(settings.MQTT_BASE_URL + "/send-first-media-message", json=json.dumps(data), headers={"Content-Type": "application/json"})
        #         print("coming in as json")
        #     except Exception as error:
        #         print(error)
        print(response.status_code)
        if response.status_code == 200:
            # add user to unwanted accounts to avoid sending them messages again
            # set the status to sent_compliment to show they have been reached out to
            # create a thread if it does not exist and then create the message
            # if the thread exists filter it out and then add the appropriate message
            try:
                UnwantedAccount.objects.create(username=account.igname)
            except Exception as err:
                print(err)
            sent_compliment_status = StatusCheck.objects.get(name="sent_compliment")
            account.status = sent_compliment_status
            account.outreach_success = True
            account.outreach_time = timezone.now()
            # account.assigned_to = "Human" # NB: do not forget to handle this from prompt level
            account.save()
            print(f"response============{response}")
            try:

                print(f"json======================{response.json()}")
                returned_data = response.json()

                try:
                    thread_obj = Thread.objects.create(thread_id=returned_data["thread_id"])
                    thread_obj.thread_id = returned_data["thread_id"]
                    thread_obj.account = account
                    thread_obj.last_message_content = first_message
                    thread_obj.unread_message_count = 0
                    thread_obj.last_message_at = datetime.fromtimestamp(int(returned_data['timestamp'])/1000000) # use UTC
                    thread_obj.save()

                    message = Message()
                    message.content = first_message
                    message.sent_by = "Robot"
                    message.sent_on = datetime.fromtimestamp(int(returned_data["timestamp"]) / 1000000)
                    message.thread = thread_obj
                    message.save()
                    print("message created then saved")
                except Exception as error:
                    print(error)
                    try:
                        thread_obj = Thread.objects.filter(thread_id=returned_data["thread_id"]).latest('created_at')
                        thread_obj.thread_id = returned_data["thread_id"]
                        thread_obj.account = account
                        thread_obj.last_message_content = first_message
                        thread_obj.unread_message_count = 0
                        thread_obj.last_message_at = datetime.fromtimestamp(int(returned_data['timestamp'])/1000000) # use UTC
                        thread_obj.save()

                        message = Message()
                        message.content = first_message
                        message.sent_by = "Robot"
                        message.sent_on = datetime.fromtimestamp(int(returned_data["timestamp"]) / 1000000)
                        message.thread = thread_obj
                        message.save()
                        print("message is saved")
                    except Exception as error:
                        print(error)
            except Exception as error:
                print(error)
                print("message not saved")
            
            try:
                subject = 'Hello Team'
                message = f'Outreach for {account.igname} has been sent'
                from_email = 'lutherlunyamwi@gmail.com'
                recipient_list = ['lutherlunyamwi@gmail.com','tomek@boostedchat.com']
                send_mail(subject, message, from_email, recipient_list)
                notify_click_up_tech_notifications(comment_text=message,notify_all=True)
                # ADD CLICKUP TASK HERE
                try:
                    if not account.question_asked:
                        create_click_up_task(f"Follow up with {account.igname}", "", True)
                        account.question_asked = True
                        account.save()
                except Exception as error:
                    print(error)
                
            except Exception as error:
                print(error)
        
    
    send()

        # raise Exception("There is something wrong with mqtt")


@shared_task()
@schema_context(os.getenv("SCHEMA_NAME"))
def send_test_compliment(username, message, repeat=True):
    # check if now is within working hours
    # if not_in_interval():
    #     err_str = f"{username} scheduled at wrong time"
    #     outreachErrorLogger(None, None, err_str, 422, "ERROR", "Time", False) # we can not do anything about the time. Do not reschedule

    numTries = 0
    print("Searching for:::>>>>>> ", username)
    # account = get_account(username)
    account = None
    accounts = Account.objects.filter(igname__icontains=username[0]).exclude(status__name='sent_compliment')
    if accounts.exists():
        account = accounts.latest('created_at')
        if not account.salesrep_set.exists():
            assign_salesrep(account)

    if account is None:
        err_str = f"{username} account does not exist"
        outreachErrorLogger(None, None, err_str, 404, "ERROR", "Lead", True)  # reshedule_next
        # raise Exception(err_str)

    print("Found Account:::>>>>>> ", account)
    thread_obj = None

    account.status_param = 'Prequalified'
    # account.outreach_time = target_time
    account.save()

    # thread_exists = ig_thread_exists(username)
    # if thread_exists:
    #     outreachErrorLogger(account, None, "Already has thread", 422, "ERROR", "Lead", True) # reshedule_next

    # check that account has sales_rep
    check_value = account_has_sales_rep(account)

    if not check_value:
        err_str = f"{username} has no sales rep assigned"
        outreachErrorLogger(account, None, err_str, 404, "ERROR", "Sales Rep", True)  # reshedule_next
        outreachErrorLogger(err_str)
        raise Exception(err_str)

    account_sales_rep_ig_name = check_value
    check_value = sales_rep_is_available(account)
    if not check_value:
        err_str = f"{account_sales_rep_ig_name} sales rep set for {username} is not available"
        outreachErrorLogger(account, None, err_str, 422, "ERROR", "Sales Rep",
                            False)  # Nothing to be done. No action on our part can make it available
        # outreachErrorLogger(err_str)
        # raise Exception(f"{account_sales_rep_ig_name} sales rep set for {username} is not available")

    salesrep = account.salesrep_set.first()
    if not isMQTTUP():
        outreachErrorLogger(account, salesrep, "MQTT service unavailable. Not handled", 503, "ERROR", "MQTT",
                            False)  # Nothinig to be done. No action on our part can bring it up
    # check if sales_rep is logged_in
    # try:
    #     logged_in = sales_rep_is_logged_in(account, salesrep)
    #     if not logged_in: # log in will need to be handled differently from the others
    #         err_str = f"{account_sales_rep_ig_name} sales rep set for {username} is not logged in"
    #         outreachErrorLogger(account, salesrep, err_str, 403, "WARNING", "Sales Rep IG", False)  # WARNING will not break execution
    #         if not logout_and_login(account, salesrep): # Nothing to be done. We cannot try logging in constantly
    #             return # nothing to do. Wait for the account to be logged back in manually.

    # except Exception as e:
    #     print(f"An error occurred: {e}")
    #     return

    # try:
    #     ig_account_exists = user_exists_in_IG(account, salesrep)
    #     if not ig_account_exists: # log in will need to be handled differently from the others
    #         # delete_first_compliment_task(account)
    #         err_str = f"{username} does not exist"
    #         outreachErrorLogger(account, salesrep, err_str, 404, "ERROR", "Lead", True)  # WARNING will break execution and reschedule another

    # except Exception as e:
    #     print(f"An error occurred: {e}")  # probably an auth error
    #     # return
    # check also if available(1)

    # for development: throw this error:
    # raise Exception("...There is something wrong with mqtt...")

    # full_name = "there"
    # print(f'Account: {account}')
    # try:
    #     full_name = format_full_name(account.full_name)
    # except Exception as error:
    #     print(error)

    # raise Exception("There is something wrong with mqt----t")
    outsourced_data = OutSourced.objects.filter(account=account)
    results = None
    try:
        if isinstance(outsourced_data.last().results, str):
            results = eval(outsourced_data.last().results)
        else:
            results = outsourced_data.last().results
    except:
        results = {"media_id": "", "media_comment": ""}
    print(f"results================{results}")
    print(f"results================MMM")
    print(f"results================{message}")
    first_message = None
    try:
        first_message = get_gpt_response(account, message)
    except Exception as err:
        logging.warning(f"error: {err}")

    media_id = results.get("media_id", "")
    data = {"username_from": salesrep.ig_username, "message": first_message, "username_to": account.igname,
            "mediaId": media_id}

    # like and comment
    is_like_and_comment = like_and_comment(media_id=media_id, media_comment=results.get("media_comment", ""),
                                           salesrep=salesrep, account=account)
    if is_like_and_comment:
        time.sleep(60)  # we break for 1 minute then send message
        print("successfully liked and commented")

    print(f"data=============={data}")
    print(f"data=============={json.dumps(data)}")

    def send(numTries=0):
        numTries += 1
        try:
            # TODO: authenticate this mqtt request
            response = requests.post(settings.MQTT_BASE_URL + "/send-first-media-message", data=json.dumps(data),
                                     headers={"Content-Type": "application/json"})
            print("coming in as data")
        except Exception as error:
            try:
                # TODO: authenticate this mqtt request
                response = requests.post(settings.MQTT_BASE_URL + "/send-first-media-message", json=json.dumps(data),
                                         headers={"Content-Type": "application/json"})
                print("coming in as json")
            except Exception as error:
                print(error)
        print(response.status_code)
        if response.status_code == 200:
            # add user to unwanted accounts to avoid sending them messages again
            # set the status to sent_compliment to show they have been reached out to
            # create a thread if it does not exist and then create the message
            # if the thread exists filter it out and then add the appropriate message
            try:
                UnwantedAccount.objects.create(username=account.igname)
            except Exception as err:
                print(err)
            sent_compliment_status = StatusCheck.objects.get(name="sent_compliment")
            account.status = sent_compliment_status
            account.outreach_success = True
            account.outreach_time = timezone.now()
            # account.assigned_to = "Human" # NB: do not forget to handle this from prompt level
            account.save()
            print(f"response============{response}")
            try:

                print(f"json======================{response.json()}")
                returned_data = response.json()

                try:
                    thread_obj = Thread.objects.create(thread_id=returned_data["thread_id"])
                    thread_obj.thread_id = returned_data["thread_id"]
                    thread_obj.account = account
                    thread_obj.last_message_content = first_message
                    thread_obj.unread_message_count = 0
                    thread_obj.last_message_at = datetime.fromtimestamp(
                        int(returned_data['timestamp']) / 1000000)  # use UTC
                    thread_obj.save()

                    message = Message()
                    message.content = first_message
                    message.sent_by = "Robot"
                    message.sent_on = datetime.fromtimestamp(int(returned_data["timestamp"]) / 1000000)
                    message.thread = thread_obj
                    message.save()
                    print("message created then saved")
                except Exception as error:
                    print(error)
                    try:
                        thread_obj = Thread.objects.filter(thread_id=returned_data["thread_id"]).latest('created_at')
                        thread_obj.thread_id = returned_data["thread_id"]
                        thread_obj.account = account
                        thread_obj.last_message_content = first_message
                        thread_obj.unread_message_count = 0
                        thread_obj.last_message_at = datetime.fromtimestamp(
                            int(returned_data['timestamp']) / 1000000)  # use UTC
                        thread_obj.save()

                        message = Message()
                        message.content = first_message
                        message.sent_by = "Robot"
                        message.sent_on = datetime.fromtimestamp(int(returned_data["timestamp"]) / 1000000)
                        message.thread = thread_obj
                        message.save()
                        print("message is saved")
                    except Exception as error:
                        print(error)
            except Exception as error:
                print(error)
                print("message not saved")

            try:
                subject = 'Hello Team'
                message = f'Outreach for {account.igname} has been sent'
                from_email = 'lutherlunyamwi@gmail.com'
                recipient_list = ['lutherlunyamwi@gmail.com']
                send_mail(subject, message, from_email, recipient_list)
                # notify_click_up_tech_notifications(comment_text=message, notify_all=True)
                # ADD CLICKUP TASK HERE
                # try:
                #     if not account.question_asked:
                #         create_click_up_task(f"Follow up with {account.igname}", "", True)
                #         account.question_asked = True
                #         account.save()
                # except Exception as error:
                #     print(error)

            except Exception as error:
                print(error)

        else:
            # get last account in queue
            # delay 2 minutes
            # send

            # TODO: Follow the example below so that we can adopt the object oriented paradigm,
            # and increase the team as a result increasing thoroughput
            # study the article below as we continue refactoring the codebase https://refactoring.guru/refactoring/what-is-refactoring

            # exception = ExceptionModel.objects.create(
            #     code = response.status_code,
            #     affected_account = account,
            #     data = {"igname": salesrep.ig_username},
            #     error_message = response.text
            # )
            # message = ""
            # send_first_compliment(get_account(),
            #                       message)  # recurse to the next individual TODO: place a check to determine if the
            # user exist
            # ExceptionHandler(exception.status_code).take_action(data=exception.data)
            print(f"Request failed with status code: {response.status_code}")
            print(f"Response message: {response.text}")
            # try:
            #     username_to = data.get("username_to", "Unknown")
            #     # notify_click_up_tech_notifications(comment_text=f"message: {response.text} username: {username_to}",
            #                                        notify_all=True)
            # except error:
            #     pass
            # sav
            # response = requests.post(f"{os.getenv('API_URL')}/serviceManager/restart-container/",
            #                          headers={'Content-Type': 'application/json'},
            #                          data=json.dumps({"container_id":"boostedchat-site-mqtt-1"}))

            # if response.status_code in [200,201]:
            #     logging.warning("Succesfully restarted mqtt")
            # repeatLocal = handleMqTTErrors(account, salesrep, response.status_code, response.text, numTries, repeat)
            # if repeatLocal and numTries <= 1:
            # send(numTries)
            # pass

    send()

    # raise Exception("There is something wrong with mqtt")


@shared_task()
@schema_context(os.getenv("SCHEMA_NAME"))
def send_report():
    yesterday = timezone.now().date() - timezone.timedelta(days=1)
    yesterday_start = timezone.make_aware(timezone.datetime.combine(yesterday, timezone.datetime.min.time()))

    threads = Thread.objects.filter(created_at__gte=yesterday_start)

    messages = []

    for thread in threads:
        for message in thread.message_set.all():
            messages.append({
                "sent_by":message.sent_by,
                "sent_at":message.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "content":message.content,
                "assigned": thread.account.assigned_to,
                "username": thread.account.igname,
                "active_stage": thread.account.status_param
            })
    try:
        subject = 'Hello Team'
        message = f'Here are the outreach results for the previous day {json.dumps(messages)}'
        from_email = 'lutherlunyamwi@gmail.com'
        recipient_list = ['lutherlunyamwi@gmail.com','tomek@boostedchat.com']
        send_mail(subject, message, from_email, recipient_list)
        notify_click_up_tech_notifications(comment_text=message,notify_all=True)
    except Exception as error:
        print(error)



@shared_task()
@schema_context(os.getenv("SCHEMA_NAME"))
def generate_response_automatic(query, thread_id):
    thread = Thread.objects.filter(thread_id=thread_id).latest('created_at')
    account = Account.objects.filter(id=thread.account.id).latest('created_at')
    print(account.id)
    thread = Thread.objects.filter(account=account).latest('created_at')

    client_messages = query.split("#*eb4*#") if query else []
    # existing_messages = Message.objects.filter(thread=thread, content__in=client_messages)
    # if existing_messages.count() == len(client_messages):
    for client_message in client_messages:
        if client_message and not Message.objects.filter(content=client_message, sent_by="Client", thread=thread).exists():
            Message.objects.create(
                content=client_message,
                sent_by="Client",
                sent_on=timezone.now(),
                thread=thread
            )
        
    if client_messages:
        # if thread.last_message_content == client_messages[len(client_messages)-1]:
        #     return {
        #         "text": query,
        #         "success": True,
        #         "username": thread.account.igname,
        #         "generated_comment": "already_responded",
        #         "assigned_to": "Robot",
        #         "status":200
        #     }    
        
        
        thread.last_message_content = client_messages[len(client_messages)-1]
        thread.unread_message_count = len(client_messages)
        thread.last_message_at = timezone.now()
        thread.save()

    if thread.account.assigned_to == "Robot":
        try:
            gpt_resp = None
            last_message = thread.message_set.order_by('-sent_on').first()
            
            


            # if last_message.content and last_message.sent_by == "Robot":
            #     gpt_resp = "already_responded"
            # else:
            gpt_resp = get_gpt_response(account, str(client_messages), thread.thread_id)
            
            thread.last_message_content = gpt_resp
            thread.last_message_at = timezone.now()
            thread.save()

            result = gpt_resp
            
            Message.objects.create(
                content=result,
                sent_by="Robot",
                sent_on=timezone.now(),
                thread=thread
            )
            print(result)
            return {
                "generated_comment": gpt_resp,
                "text": query,
                "success": True,
                "username": thread.account.igname,
                "assigned_to": "Robot",
                "status":200
            }

        except Exception as error:
            logging.warning(error)
            # send email
            try:
                subject = f'Error in generate_response_automatic for {thread.account.igname}'
                message = f'Error: {error}, this is in effort to debug what is wrong with consistent messaging'
                from_email = 'lutherlunyamwi@gmail.com'
                recipient_list = ['lutherlunyamwi@gmail.com','tomek@boostedchat.com']
                send_mail(subject, message, from_email, recipient_list)
                notify_click_up_tech_notifications(comment_text=message,notify_all=True)
            except Exception as error:
                print(error)

            return {
                "error": str(error),
                "success": False,
                "username": thread.account.igname,
                "assigned_to": "Robot",
                "status":500
            }

    elif thread.account.assigned_to == 'Human':
        return {
            "text": query,
            "success": True,
            "username": thread.account.igname,
            "generated_comment": "",
            "assigned_to": "Human",
            "status":200
        }
    # else:
    #         return {
    #             "text": query,
    #             "success": True,
    #             "username": thread.account.igname,
    #             "generated_comment": "already_responded",
    #             "assigned_to": "Robot",
    #             "status":200
    #         }

@schema_context(os.getenv("SCHEMA_NAME"))
def assign_salesrepresentative():
    
    yesterday = timezone.now().date() - timezone.timedelta(days=1)
    yesterday_start = timezone.make_aware(timezone.datetime.combine(yesterday, timezone.datetime.min.time()))
    

    # Get the list of usernames from the UnwantedAccount table
    unwanted_usernames = UnwantedAccount.objects.values_list('username', flat=True)

    
    # Create the word filters
    word_filters = Q()
    for word in STYLISTS_WORDS:
        word_filters |= Q(igname__icontains=word)  # Replace 'description' with the actual field name

    # Combine the filters and exclude unwanted accounts
    accounts = Account.objects.filter(
        Q(created_at__gte=yesterday_start) & word_filters
    ).exclude(
        status__name="sent_compliment"
    ).exclude(
        igname__in=unwanted_usernames
    ) 

    
    for lead in accounts:
        lead.qualified = False
        lead.save()
        if not lead.thread_set.exists():
            # first check is the outsourced and relevant information
            try:
                oso = OutSourced.objects.get(account__id=lead.id)
                try:
                    if isinstance(oso.results,str):
                        oso.results = json.loads(json.dumps(oso.results))
                        oso.save()
                except Exception as err:
                    print(err)
                lead.relevant_information = oso.results
                lead.save()
                
                # pass him over to unwanted accounts
            except OutSourced.DoesNotExist:
                print("OutSourced does not exist")
            
            
            # Get all sales reps
            sales_reps = SalesRep.objects.filter(available=True)

            # Calculate moving averages for all sales reps
            sales_rep_moving_averages = {
                sales_rep: get_moving_average(sales_rep) for sales_rep in sales_reps
            }


            # Find the sales rep with the minimum moving average
            best_sales_rep = min(sales_rep_moving_averages, key=sales_rep_moving_averages.get)
            best_sales_rep.instagram.add(lead)
            # Assign the lead to the best sales rep
            #lead.assigned_to = best_sales_rep
            #lead.save()
            best_sales_rep.save()
            # Record the assignment in the history
            LeadAssignmentHistory.objects.create(sales_rep=best_sales_rep, lead=lead)
    #         endpoint = "https://mqtt.booksy.us.boostedchat.com"

    #         srep_username = best_sales_rep.ig_username
    #         if lead.thread_set.exists():
    #             thread = lead.thread_set.latest('created_at')
    #             response = requests.post(f'{endpoint}/approve', json={'username_from': srep_username,'thread_id':thread.thread_id})
                
    #             # Check the status code of the response
    #             if response.status_code == 200:
    #                 print('Request approved')
    #             else:
    #                 print(f'Request failed with status code {response.status_code}')

    #         # send first compliment
    #         # send_compliment_endpoint = "https://api.booksy.us.boostedchat.com/v1/instagram/sendFirstResponses/"
    #         # send_compliment_endpoint = "http://127.0.0.1:8000/v1/instagram/sendFirstResponses/"
    #         # # import pdb;pdb.set_trace()
    #         # response = requests.post(send_compliment_endpoint)
    #         # if response.status_code in [200,201]:
    #         #     print("Successfully set outreach time for compliment and will send at appropriate time")

    #         else:
    #             logging.warning("not going through")
    # send_compliment_endpoint = "https://api.booksy.us.boostedchat.com/v1/instagram/sendFirstResponses/"
    # # send_compliment_endpoint = "http://127.0.0.1:8000/v1/instagram/sendFirstResponses/"
    # # import pdb;pdb.set_trace()
    # response = requests.post(send_compliment_endpoint)
    # if response.status_code in [200,201]:
    #     print("Successfully set outreach time for compliment and will send at appropriate time")

    return {"message":"Successfully assigned salesrep","status": 200}


@shared_task()
@schema_context(os.getenv("SCHEMA_NAME"))
def reschedule():
    #reassign time slots
    times = OutreachTime.objects.filter(time_slot__gte=timezone.now()-timezone.timedelta(days=1))
    for time in times:
        time.account_to_be_assigned = None
        time.save()
    #reassign tasks

    # Step 1: Fetch tasks
    batch_size = 300  
    tasks = PeriodicTask.objects.filter(enabled=True).order_by('-id')[:batch_size*2]

    # Step 2: Initialize variables for scheduling
    current_date = timezone.now()
    current_day = current_date.day
    current_month = current_date.month

    # Step 3: Schedule tasks in batches
    for i in range(0, len(tasks), batch_size):
        # Get the current batch of tasks
        batch = tasks[i:i + batch_size]
        
        # Calculate the scheduled day for this batch
        scheduled_day = current_day + (i // batch_size)
        
        # Handle month overflow if necessary
        if scheduled_day > 31:
            scheduled_day -= 31
            current_month += 1
        
        # If month exceeds December, reset to January and increment year if needed
        if current_month > 12:
            current_month = 1
            # Increment year if necessary (not shown here, but you can track years as needed)

        for task in batch:
            sched = CrontabSchedule.objects.get(id=task.crontab.id)
            
            # Update the schedule with the new day and month
            sched.day_of_month = str(scheduled_day)
            sched.month_of_year = str(current_month)
            
            # Save the updated schedule
            sched.save()

@shared_task()
@schema_context(os.getenv("SCHEMA_NAME"))
def prequalify_task():
    prequalifying_automatically()


# @shared_task()
# @schema_context(os.getenv("SCHEMA_NAME"))
# def prequalify_task():

#     # yesterday = timezone.now().date() - timezone.timedelta(days=1)
#     # yesterday_start = timezone.make_aware(timezone.datetime.combine(yesterday, timezone.datetime.min.time()))
#     # unwanted_usernames = UnwantedAccount.objects.values_list('username', flat=True)

#     # # Filter accounts that are qualified and created from yesterday onwards, and exclude accounts that are not wanted
#     # accounts = Account.objects.filter(
#     #     Q(qualified=False) & Q(created_at__gte=yesterday_start)
#     # ).exclude(
#     #     status__name="sent_compliment"
#     # ).exclude(
#     #     igname__in=unwanted_usernames
#     # )
#     yesterday = timezone.now().date() - timezone.timedelta(days=1)
#     tomorrow = timezone.now().date() + timezone.timedelta(days=1)
#     yesterday_start = timezone.make_aware(timezone.datetime.combine(yesterday, timezone.datetime.min.time()))
#     unwanted_usernames = UnwantedAccount.objects.values_list('username', flat=True)

#     # Filter accounts that are qualified and created from yesterday onwards, and exclude accounts that are not wanted
#     accounts = Account.objects.filter(
#         Q(qualified=True) & Q(created_at__gte=yesterday_start) & Q(created_at__lte=tomorrow)
#     ).exclude(
#         status__name="sent_compliment"
#     ).exclude(
#         igname__in=unwanted_usernames
#     )
#     if accounts.exists():
#     # TODO: either recurse or use a while loop to iteratively pick the
#     # next set of accounts until the prequalified accounts reach 25.  
#         for account in accounts:
#             if account.salesrep_set.exists():
#                 pass
#             else:
#                 logging.warning(f"Account {account.igname} has no sales rep assigned, reassigning account")
#                 assign_salesrep(account)
#             try:
#                 payload = {
#                     "department":"Prequalifying",
#                     "agent_name":"Qualifying Agent",
#                     "agent_task":"QD_QualifyingA_CalculatePersonaInfluencerAuditQualifyingScoreT",
#                     "converstations":"",
#                     "Scraped":{
#                         "message":"",
#                         "sales_rep":account.salesrep_set.filter(available=True).latest('created_at').ig_username,   
#                         "influencer_ig_name":account.salesrep_set.filter(available=True).latest('created_at').ig_username,   
#                         "outsourced_info":account.outsourced_set.latest('created_at').results,
#                         "relevant_information":account.relevant_information
#                     }
#                 }
                
#                 setup_agent_workflow(payload=payload)
#                 if account.qualified:
#                     account.dormant_profile_created = True
#                 account.save()
#             except Exception as error:
#                 logging.warning(error)
        
#         try:
#             subject = 'Hello Team'
#             message = f'Finished prequalifying accounts for today {timezone.now()}'
#             from_email = 'lutherlunyamwi@gmail.com'
#             recipient_list = ['lutherlunyamwi@gmail.com','tomek@boostedchat.com']
#             send_mail(subject, message, from_email, recipient_list)
#             notify_click_up_tech_notifications(comment_text=message,notify_all=True)
#         except Exception as error:
#             print(error)
            
            
@shared_task()
def scrap_followers(username,delay,round_):
    inst = InstagramSpider(load_tables=load_tables,db_url=db_url)
    inst.scrap_followers(username,delay,round_=round_)

@shared_task()
def scrap_users(query,round_,index):
    inst = InstagramSpider(load_tables=load_tables,db_url=db_url)
    inst.scrap_users(query,round_=round_,index=index)
    
@shared_task()
def scrap_info(delay_before_requests,delay_after_requests,step,accounts,round_):
    inst = InstagramSpider(load_tables=load_tables,db_url=db_url)
    inst.scrap_info_v1(delay_before_requests,delay_after_requests,step,accounts,round_)
    load_info_to = 1
    if load_info_to == 1:
        load_info_to_database()
    elif load_info_to == 2:
        load_info_to_csv()
    
@shared_task()
def insert_and_enrich(keywords_to_check,round_number):
    inst = InstagramSpider(load_tables=load_tables,db_url=db_url)
    inst.insert_and_enrich(keywords_to_check,round_number=round_number)


@shared_task()
def scrap_mbo():
    try:
            # Execute Scrapy spider using the command line
        subprocess.run(["scrapy", "crawl", "mindbodyonline"])
        
    except Exception as e:
        print(e)
    

def qualify_algo(client_info,keywords_to_check):
    keyword_found = None
    if client_info:
            keyword_counts = {keyword: 0 for keyword in keywords_to_check}

            # Iterate through the values in client_info
            for value in client_info.values():
                # Iterate through the keywords to check
                for keyword in keywords_to_check:
                    # Count the occurrences of the keyword in the value
                    keyword_counts[keyword] += str(value).lower().count(keyword.lower())

            # Check if any keyword has more than two occurrences
            keyword_found = any(count >= 1 for count in keyword_counts.values())
    return keyword_found

@shared_task()
@schema_context(os.getenv("SCHEMA_NAME"))
def load_info_to_csv():
    try:
        prequalified = pd.read_csv('prequalified.csv')
        df = prequalified.reset_index()
        for i,user in enumerate(df['level_1']):
            try:
                db_user = InstagramUser.objects.filter(username=user).latest('created_at')
                print(user)
                try:
                    df.at[i,'outsourced_info'] = db_user.info
                except Exception as err:
                    print(err,'---->outsourced_info_error')
                try:
                    df.at[i,'relevant_information'] = db_user.info
                except Exception as err:
                    print(err,'---->relevant infof error')
            except Exception as err:
                print(err,f'---->user--{user} not found')
        df.to_csv('prequalified.csv',index=False)
    except Exception as err:
        print(err,"file not found")  


def get_headers():
    headers = {
        'Content-Type': 'application/json'
    }
    return headers

def update_account_information(user:InstagramUser):
    cl = initialize_hikerapi_client()
    profile_information,user_media = None
    try:
        profile_information = cl.user_by_username_v1(user.username)
        user_media = cl.user_medias(user_id=cl.user_by_username_v1(username=user.username).get("pk"),count=1)[0]
    except Exception as err:
        logging.warning(err)
        profile_information = {"username":user.username}
        user_media = {"id":user.item_id}
    headers = get_headers()
    get_id_account_data = {
        "username": user.username
    }
    response = requests.post(f"{os.getenv('API_URL')}/instagram/account/get-id/",data=get_id_account_data)
    account_id = response.json()['id']
    account_outsourced = response.json()
    account_dict = {
        "igname": user.username,
        "is_manually_triggered":True,
        "relevant_information": {**profile_information,**{"media_id": user_media.get("id")}}
    }
    response = requests.patch(
        f"{os.getenv('API_URL')}/instagram/account/{account_id}/",
        headers=headers,
        data=json.dumps(account_dict)
    )
    account = response.json()
    print(account)
    # Save outsourced data
    if "outsourced_id" in account_outsourced:
        outsourced_id = account_outsourced['outsourced_id']
        outsourced_dict = None

        if user.info:
            outsourced_dict = {
                "results": {**profile_information,**{"media_id": user_media.get("id")}},
                "source": "instagram"
            }
        else:
            outsourced_dict = {
                "results": {**profile_information,**{"media_id": user_media.get("id")}},
                "source": "instagram"
            }
        # import pdb;pdb.set_trace()
        response = requests.patch(
            f"{os.getenv('API_URL')}/instagram/outsourced/{outsourced_id}/",
            headers=headers,
            data=json.dumps(outsourced_dict)
        )
        if response.status_code in [200,201]:
            print("successfully posted outsourced data")
        else:
            print("failed to post outsourced data")
    # Save relevant data
    # if qualify_algo(user.info,STYLISTS_WORDS):

def create_account_information(user:InstagramUser):
    headers = get_headers()
    profile_information,user_media = None
    cl = initialize_hikerapi_client()
    try:
        profile_information = cl.user_by_username_v1(user.username)
        user_media = cl.user_medias(user_id=cl.user_by_username_v1(username=user.username).get("pk"),count=1)[0]
    except Exception as err:
        logging.warning(err)
        profile_information = {"username":user.username}
        user_media = {"id":user.item_id}
        
    account_dict = {
        "igname": user.username,
        "is_manually_triggered":True,
        "relevant_information": {**profile_information,**{"media_id": user_media.get("id")}}
    }
    response = requests.post(
        f"{os.getenv('API_URL')}/instagram/account/",
        headers=headers,
        data=json.dumps(account_dict)
    )
    account = response.json()
    print(account)
    # Save outsourced data
    outsourced_dict = None

    if user.info:
        outsourced_dict = {
            "results": {**profile_information,**{"media_id": user_media.get("id")}},
            "source": "instagram"
        }
    else:
        outsourced_dict = {
            "results": {**profile_information,**{"media_id": user_media.get("id")}},
            "source": "instagram"
        }
    # import pdb;pdb.set_trace()
    response = requests.post(
        f"{os.getenv('API_URL')}/instagram/account/{account['id']}/add-outsourced/",
        headers=headers,
        data=json.dumps(outsourced_dict)
    )
    if response.status_code in [200,201]:
        print("successfully posted outsourced data")
    else:
        print("failed to post outsourced data")
    # Save relevant data
    # if qualify_algo(user.info,STYLISTS_WORDS):
    try:
        inbound_qualify_data = {
            "username": user.username,
            "qualify_flag": False,
            "relevant_information": json.dumps(user.relevant_information),
            "scraped":True
        }
        response = requests.post(f"{os.getenv('API_URL')}/instagram/account/qualify-account/",data=inbound_qualify_data)

        if response.status_code in [200,201]:
            print(response.json())
            print(f"Account-----{user.username} successfully qualified")
    except Exception as err:
        print(err,f"---->error in qualifying user {user.username}")  

@shared_task()
@schema_context(os.getenv("SCHEMA_NAME"))
def load_info_to_database():
    
    try:
        yesterday = timezone.now() - timezone.timedelta(days=1)
        yesterday_start = timezone.make_aware(timezone.datetime.combine(yesterday,timezone.datetime.min.time()))

        instagram_users = None
        try:
            response = requests.post(
                f"{os.getenv('API_URL')}/instagram/getOutreachAccounts/",
                headers={"Content-Type": "application/json"},
                data={}
            )
            accounts_ = response.json()['accounts']
            instagram_users = InstagramUser.objects.filter(username__in=[account['igname'] for account in accounts_]).distinct('username')  
            print(f"found the following number of instagram accounts: {instagram_users.count()}")
        except Exception as error:
            logging.warning(error)
        if instagram_users.exists():
            pass
        else:
            instagram_users = InstagramUser.objects.filter(created_at__gte=yesterday_start).distinct('username')
        for user in instagram_users:
            try:
                user_exists = False
                check_accounts_endpoint = f"{os.getenv('API_URL')}/instagram/checkAccountExists/"
                check_data = {
                    "username": user.username
                }
                check_account_response = requests.post(check_accounts_endpoint,data=check_data)
                if check_account_response.json()['exists']:
                    user_exists = True
                if user_exists:
                    update_account_information(user) # uses patch
                else:
                    create_account_information(user) # uses post
                
            except Exception as err:
                print(err, f"---->error in posting user {user.username}")
    except Exception as err:
        print(err, "---->error in posting data")


def log_scrapping_logs(self, log_file_path):
    """Logs the contents of scrappinglogs.txt to W&B and deletes the file."""
    try:
        with open(log_file_path, 'r') as file:
            logs = file.read()
            # Log the entire content of the log file
            wandb.log({"scrapping_logs": logs})
            print("Scrapping logs logged successfully.")
        
        # Delete the log file after logging
        os.remove(log_file_path)
        print(f"{log_file_path} has been deleted.")
    
    except Exception as e:
        print(f"Error logging scrapping logs: {e}")

class WandbLoggingHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        wandb.log({"langchain_log": log_entry})

@shared_task
def send_logs(data,result):
    logging_filename = f"scrappinglogs-{str(uuid.uuid4())}.txt"
    with wandb.init(
            project="boostedchat",  # replace with your WandB project name
            entity="lutherlunyamwi",       # replace with your WandB username or team
            name=f"crewai_run_{data.get('department')}",  # custom name for each run
            config=data           # optionally log the request data as run config
        ) as run:
        wandb_handler = WandbLoggingHandler()
        wandb_handler.setLevel(logging.INFO)
        wandb_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

        langchain_logger = logging.getLogger("langchain")
        langchain_logger.addHandler(wandb_handler)
        langchain_logger.setLevel(logging.INFO)
        

        wandb.log({"result": result})  # log the final result

        

        # End wandb run
        time.sleep(2)
        log_scrapping_logs(logging_filename)
        wandb.finish()




@shared_task()
def scrap_media(media_links=None):
    inst = InstagramSpider(load_tables=load_tables,db_url=db_url)
    inst.scrap_media(media_links)
    

@shared_task()
def fetch_request(url):
    response = requests.Request(url)
    return response.json()



@shared_task()
def scrap_hash_tag(hashtag):
    inst = InstagramSpider(load_tables=load_tables,db_url=db_url)
    inst.scrap_hashtag(hashtag)



@shared_task()
@schema_context(os.getenv("SCHEMA_NAME"))
def relogin_scouts(selected_scouts=None):
    
    with schema_context(os.getenv("SCHEMA_NAME")):
        updated_count = 0
        scouts = Scout.objects.filter(id__in=selected_scouts)
        for scout in scouts:
            try:
                client = login_user(scout)
                scout.available = True
                scout.save()
                updated_count += 1
            except Exception as e:
                print(e)
                scout.available = False
                scout.save()
                updated_count += 1  # Count even if an exception occurred

@shared_task()
@schema_context(os.getenv("SCHEMA_NAME"))
def load_info_to_database_v2():
    print(InstagramUser.objects.filter(created_at__gte=timezone.now()-timezone.timedelta(days=1)).count())
    instagram_users = InstagramUser.objects.filter(created_at__gte=timezone.now()-timezone.timedelta(days=1))
    for user in instagram_users:
        account =  Account.objects.create(igname=user.username,relevant_information=user.info if user.info else {"media_id":user.item_id,"username":user.username})
        outsourced = OutSourced.objects.create(results=user.info if user.info else {"media_id":user.item_id,"username":user.username},account=account)
    return


@shared_task()
def qualify_and_reschedule():
    with schema_context(os.environ.get("SCHEMA_NAME")):
        barber_keywords = [
        "hair",
        "appointment",
        "appointments",
        "book",
        "call",
        "book.thecut.co",
        "licensed",
        "cutz",
        "kutz",
        "cuts",
        "cut",
        "hairstylist",
        "salon",
        "salons",
        "educator",
        "specialist",
        "beauty",
        "barber",
        "walk",
        "text",
        "stylist",
        "colour",
        "colouring",
        "loreal",
        "olaplex",
        "hairspray",
        "mousse",
        "pomade",
        "hair oil",
        "hair serum",
        "scissors",
        "fades",
        "fade",
        "faded",
        "comb",
        "brush",
        "blow dryer",
        "flat iron",
        "curling iron",
        "hair rollers",
        "hair clips",
        "hair ties",
        "headbands",
        "hair accessories",
        "updos",
        "braids",
        "twists",
        "buns",
        "ponytails",
        "curls",
        "waves",
        "volume",
        "texture",
        "shine",
        "frizz control",
        "breakage",
        "dryness",
        "oiliness",
        "thinning",
        "hair loss",
        "dandruff",
        "scalp problems",
        ]

        # Create a Q object for filtering
        query = Q()
        for keyword in barber_keywords:
            query |= Q(igname__icontains=keyword)

        yesterday = timezone.now() - timezone.timedelta(days=30) # filter on a weekly basis
        unwanted_usernames = UnwantedAccount.objects.values_list('username', flat=True)
        # Filter accounts using the query
        filtered_accounts = Account.objects.filter(query).filter(created_at__gte=yesterday).exclude(status__name="sent_compliment").exclude(igname__in=unwanted_usernames).exclude(
            dormant_profile_created=True
        )

        for account in filtered_accounts:
            account.qualified = True
            account.engagement_version = "1"
            account.created_at = timezone.now()
            account.save()
        print(filtered_accounts.count())


        # Split to run for x days automatically
        number_outreach_per_day = 50
        total_outreach_days = round(filtered_accounts.count()/number_outreach_per_day)
        day_schedule_accounts = [{"day": 0}]
        day_to_schedule = 0
        accounts_index = 0




        while accounts_index < len(filtered_accounts):
            
            print(accounts_index)
            if day_schedule_accounts[-1]['day'] == total_outreach_days:
                break
            
            day_to_schedule += 1
            
            # Distribute accounts for this day
            for _ in range(number_outreach_per_day):
                if accounts_index >= len(filtered_accounts):
                    break
                day_schedule_accounts.append({
                    "day": day_to_schedule,
                    "account": filtered_accounts[accounts_index]
                })
                
                accounts_index += 1

        # Remove the initial placeholder
        if day_schedule_accounts[0]['day'] == 0 and len(day_schedule_accounts) > 1:
            day_schedule_accounts.pop(0)


        print(len(day_schedule_accounts))
        for account in day_schedule_accounts:
            account['account'].created_at = timezone.now() + timezone.timedelta(days = account['day']-1,)
            account['account'].outreach_time = timezone.now() + timezone.timedelta(days = account['day']-1)
            account['account'].save()
            # pass


        day_schedule_accounts


@shared_task()
@schema_context(os.getenv("SCHEMA_NAME"))
def get_media_likers(media_links=None):
    if not media_links:
        logging.warning("error: Media Links is required.")

    if isinstance(media_links, str):
        media_links = ast.literal_eval(media_links)

    # Initialize the HikerAPI client
    cl = initialize_hikerapi_client()
    likers_list = []
    influencers_list = ["vicblends","jrlusa","sly.huncho","robtheoriginal","barbersince98"]
    for link in media_links:
        if len(media_links) > 1:
            break
        try:
            # Fetch the likers of the media
            influencer = random.choice(influencers_list)
            logging.warning(f"influencer chosen ---->{influencer}")
            latest_influencer_media = cl.user_medias(user_id=cl.user_by_username_v1(username=influencer).get("pk"),count=1)[0]
            # media_id = cl.media_pk_from_url_v1(link)
            likers = cl.media_likers_v2(latest_influencer_media.get("pk"))
            for liker in likers['users']:
                liker_data = {
                    "username": liker['username'],
                    "full_name": liker['full_name'],
                    "profile_pic_url": liker['profile_pic_url'],
                    "is_verified": liker['is_verified']
                }
                try:
                    InstagramUser.objects.create(
                        username=liker['username'],
                        info = cl.user_by_username_v1(liker['username'])
                    )
                except Exception as e:
                    # Handle the case where the user already exists
                    print(f"User {liker.username} already exists in the database.")
                
                try:
                    account = Account.objects.create(
                        igname=liker['username'],
                        # ADD CHECK TO PRVENT BILLING JSONS FROM BEING SAVED
                        # {
                        #     "error": "Top up your account at https://hikerapi.com/billing",
                        #     "state": false,
                        #     "exc_type": "InsufficientFunds",
                        #     "media_id": null
                        # }
                        relevant_information=cl.user_by_username_v1(liker['username'])
                    )
                    user_media = cl.user_medias(user_id=cl.user_by_username_v1(username=liker['username']).get("pk"),count=1)[0]
                    OutSourced.objects.create(
                        results = {"media_id":user_media.get("id"),**cl.user_by_username_v1(liker['username'])},
                        account = account
                    )
                    logging.info(f"Account {liker['username']} created successfully.")
                except Exception as e:
                    # Handle the case where the user already exists
                    print(f"account error --> {e}")
                # Add the liker data to the list
                likers_list.append(liker_data)
            
        except Exception as e:
            logging.warning(f"error: {str(e)}")


@shared_task
@schema_context(os.getenv("SCHEMA_NAME"))
def fetch_all_followers_task(username, user_id):
    cl = initialize_hikerapi_client()
    all_followers = []
    max_id = None
    page_count = 0
    
    followers = cl.user_followers(user_id=user_id, count=7000)
    for follower in followers:
        if follower:
            try:
                # Check if the user already exists
                if Account.objects.filter(igname=follower['username']).exists():
                    print(f"User {follower['username']} already exists in the database.")
                    continue
                else:
                    account = Account.objects.create(
                        igname=follower['username'],
                        relevant_information=follower,
                        dormant_profile_created=True  # Set to True if you want to mark it as dormant
                    )
                    OutSourced.objects.create(
                        results=follower,
                        account=account
                    )
                    all_followers.append(follower['username'])
            except Exception as e:
                print(f"Error processing follower {follower['username']}: {e}")
    # while page_count < 100:  # Adjust limit as needed
        # try:
        #     if max_id:
        #         followers_chunk = cl.user_followers_chunk_v1(user_id, max_id=max_id)
        #     else:
        #         followers_chunk = cl.user_followers_chunk_v1(user_id)
            
        #     if not followers_chunk:
        #         break
            

        #     for followers in followers_chunk:
        #         if followers:
        #             for follower in followers:
        #                 logging.warning(f"Processing follower: {follower['username']} out of {len(followers_chunk)}")
        #                 try:
        #                     # Check if the user already exists
        #                     if Account.objects.filter(username=follower['username']).exists():
        #                         print(f"User {follower['username']} already exists in the database.")
        #                         continue
        #                     else:
        #                         account = Account.objects.create(
        #                             igname=follower['username'],
        #                             # relevant_information=cl.user_by_username_v1(follower['username'])
        #                             relevant_information=follower
        #                         )
        #                         OutSourced.objects.create(
        #                             # results=cl.user_by_username_v1(follower['username']),
        #                             results = follower,
        #                             account=account
        #                         )
        #                         all_followers.append(follower['username'])

        #                 except Exception:
        #                     pass  # User already exists
            
        #     # if len(followers_chunk) < 200:
        #     #     break
                
        #     max_id = followers_chunk[-1].pk if hasattr(followers_chunk[-1], 'pk') else None
        #     page_count += 1
        #     time.sleep(2)  # Rate limiting
            
        # except Exception as e:
        #     print(f"Error on page {page_count}: {e}")
        #     break
    
    return {"status": "completed", "pages_processed": page_count}




@shared_task
def remove_duplicates_task():
    with schema_context(os.getenv('SCHEMA_NAME')):
            duplicates = (
                Account.objects.values('igname')
                .annotate(igname_count=Count('igname'))
                .filter(igname_count__gt=1)
            )

            for dup in duplicates:
                accounts = Account.objects.filter(igname=dup['igname']).order_by('id')

                # Find account with status__name='sent_compliment'
                preferred = accounts.filter(status__name='sent_compliment').first()

                if not preferred:
                    # Find account with outsourced info
                    for acc in accounts:
                        if acc.outsourced_set.exists():
                            preferred = acc
                            break

                if not preferred:
                    # Keep the first one if none matched the above
                    preferred = accounts.latest('created_at')

                # Delete all others except preferred
                accounts_to_delete = accounts.exclude(id=preferred.id)
                accounts_to_delete.delete()


@shared_task()
@schema_context(os.getenv('SCHEMA_NAME'))
def generate_dag_script(workflow_id):
    # if "trigger_url" in dag_data:
        
    #     data = {
    #         "dag":[entry for entry in DagModel.objects.filter(id = workflow.dag.id).values()],
    #         "operators":[entry for entry in workflow.simplehttpoperators.values()],
    #         "data_seconds":workflow.delay_durations,
    #         "trigger_url":dag_data.get("trigger_url"),
    #         "trigger_url_expected_response":dag_data.get("trigger_url_expected_response")
    #     }
    # else:
    workflow = WorkflowModel.objects.get(id=workflow_id)
    print(workflow.workflow_type)
    print(workflow)
    dag_ = DagModel.objects.filter(workflow__id = workflow.id)
    dag = dag_.latest('created_at')
    print(dag.dag_id)
    operators = [entry for entry in dag.simplehttpoperatormodel_set.filter().values()]
    data_points = []
    for operator in operators:
        try:
            print(operator['connection_id'])
            operator['http_conn_id'] = HttpOperatorConnectionModel.objects.get(id=operator['connection_id']).connection_id
            endpoint = Endpoint.objects.get(id=operator['endpointurl_id'])
            operator['endpoint'] = endpoint.url
            operator['method'] = endpoint.method
            # Get the content type for the Endpoint model
            endpoint_content_type = ContentType.objects.get_for_model(Endpoint)
            # Query to get all custom fields and their values for the given end
            custom_fields_with_value = CustomFieldValue.objects.filter(
                content_type=endpoint_content_type,
                object_id=endpoint.id
            ).select_related('field')

            for custom_field_value in custom_fields_with_value:
                data_points.append({
                    custom_field_value.field.name: custom_field_value.value,
                    "created_at": custom_field_value.created_at
                })

            operator['data'] = remove_timestamp(flatten_dict_list(merge_lists_by_timestamp(data_points)))
            
        except Exception as error:
            print(str(error))

    dags = [entry for entry in dag_.values()]
    for x in dags:
        x['http_conn_id'] = HttpOperatorConnectionModel.objects.get(id=x['connection_id']).connection_id

    data = {
        "dag":dags,
        "operators":operators,
        "data_seconds":[str(workflow.delay_durations)]
    }

    print(dag.dag_id)
    # print(data)
    # Write the dictionary to a YAML file
    yaml_file_path = os.path.join(settings.BASE_DIR, 'api', 'helpers', 'include', 'dag_configs', f"{dag.dag_id}_config.yaml")
    with open(yaml_file_path, 'w') as yaml_file:
        try:
            yaml.dump(data, yaml_file, default_flow_style=False)
        except Exception as error:
            print(str(error))

    try:
        generate_dag(workflow_type=workflow.workflow_type)
    except Exception as error:
        print(str(error))


