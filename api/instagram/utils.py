import os
import json
import yaml
import logging
import pandas as pd
import random
import requests

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db.models import Q
from api.instagram.models import Account, Message, OutSourced, StatusCheck, Thread, UnwantedAccount,ChatSession
from api.prompt.models import Prompt
from django.conf import settings

from django_tenants.utils import schema_context
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from rest_framework.response import Response
from api.sales_rep.models import SalesRep
from rest_framework import status
from hikerapi import Client, AsyncClient
from datetime import datetime, timedelta
from celery import shared_task
from instagrapi import Client as InstaClient, exceptions

def login_user(username=None, password=None):
    cl = InstaClient()
    try:
        cl.login(username, password)
        return cl
    except exceptions.BadPassword as e:
        logging.error(f"Bad password for {username}: {e}")
    except exceptions.ChallengeRequired as e:
        logging.error(f"Challenge required for {username}: {e}")
    except exceptions.TwoFactorRequired as e:
        logging.error(f"Two-factor authentication required for {username}: {e}")
    except exceptions.ClientError as e:
        logging.error(f"Client error for {username}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error for {username}: {e}")
    return None

@schema_context(os.getenv('SCHEMA_NAME'))
def assign_salesrep(account):
    salesrep = None
    try:
        available_sales_reps = SalesRep.objects.filter(available=True)
        random_salesrep_index = random.randint(0,len(available_sales_reps)-1)
        available_sales_reps[random_salesrep_index].instagram.add(account)
        salesrep = available_sales_reps[random_salesrep_index]
    except Exception as err:
        print(err)
    return salesrep


@schema_context(os.getenv('SCHEMA_NAME'))
def get_account(usernames=None):
    """
    Recursively iterates through a list of usernames to find a suitable account.
    If no usernames are provided, it fetches the qualified usernames internally.

    Args:
        usernames (list, optional): A list of usernames to check. Defaults to None.

    Returns:
        Account or None: An Account object if found, otherwise None.
    """
    yesterday = timezone.now().date() - timezone.timedelta(days=1)
    tomorrow = timezone.now().date() + timezone.timedelta(days=1)
    yesterday_start = timezone.make_aware(timezone.datetime.combine(yesterday, timezone.datetime.min.time()))
    unwanted_usernames = UnwantedAccount.objects.values_list('username', flat=True)

    # Filter accounts that are qualified and created from yesterday onwards, and exclude accounts that are not wanted
    accounts = Account.objects.filter(
        Q(qualified=True) & Q(created_at__gte=yesterday_start) & Q(created_at__lte=tomorrow)
    ).exclude(
        status__name="sent_compliment"
    ).exclude(
        igname__in=unwanted_usernames
    ).filter(dormant_profile_created=True)

    usernames_list = list(accounts.values_list('igname', flat=True))
    if usernames is None or usernames not in usernames_list:
        # Fetch qualified usernames internally
        yesterday = timezone.now().date() - timezone.timedelta(days=1)
        tomorrow = timezone.now().date() + timezone.timedelta(days=1)
        yesterday_start = timezone.make_aware(timezone.datetime.combine(yesterday, timezone.datetime.min.time()))
        unwanted_usernames = UnwantedAccount.objects.values_list('username', flat=True)

        # Filter accounts that are qualified and created from yesterday onwards, and exclude accounts that are not wanted
        accounts = Account.objects.filter(
            Q(qualified=True) & Q(created_at__gte=yesterday_start) & Q(created_at__lte=tomorrow)
        ).exclude(
            status__name="sent_compliment"
        ).exclude(
            igname__in=unwanted_usernames
        ).filter(dormant_profile_created=True)

        usernames = list(accounts.values_list('igname', flat=True))
        random.shuffle(usernames)  # Shuffle the usernames to randomize the selection

    if not usernames:
        return None  # Base case: no usernames left to check


    username = usernames.pop(0)  # Get the first username from the list

    # Check if the username is unwanted
    check_unwanted = UnwantedAccount.objects.filter(username__icontains=username.split('-')[0])
    if check_unwanted.exists():
        # Skip this username and recurse with the remaining list
        return get_account(usernames)

    try:
        accounts = Account.objects.filter(igname__icontains=username.split('-')[0]).exclude(status__name='sent_compliment')
        if accounts.exists():
            account = accounts.latest('created_at')
            if not account.salesrep_set.exists():
                assign_salesrep(account)
            return account
        else:
            # No account found for this username, recurse with remaining usernames
            return get_account(usernames)

    except Exception as error:
        print(f"Error processing username {username}: {error}")
        # On error, recurse with remaining usernames
        return get_account(usernames)


# @schema_context(os.getenv('SCHEMA_NAME'))
# def get_account(username):
#     account = None
#     check_unwanted = UnwantedAccount.objects.filter(username__icontains=''.join(username).split('-')[0])
#     if check_unwanted.exists():
#         return 
#     try:
#         accounts = Account.objects.filter(igname__icontains=''.join(username).split('-')[0]).exclude(status__name='sent_compliment') 
#         account = accounts.latest('created_at')
#         if account.salesrep_set.exists():
#             account = account
#         else:
#             assign_salesrep(account)
            

#     except Exception as error:
#         print(error)

#     # if account is None:
#     #     get_account(username)
#     return account

@schema_context(os.getenv('SCHEMA_NAME'))
def get_account_for_salesrep(username):
    account = None
    try:
        accounts = Account.objects.filter(igname__icontains=''.join(username).split('-')[0])
        account = accounts.latest('created_at')
        if account.salesrep_set.exists():
            account = account
        else:
            assign_salesrep(account)
            

    except Exception as error:
        print(error)
    return account

@schema_context(os.getenv('SCHEMA_NAME'))
def get_sales_rep_for_account(username):
    salesrep = None
    username = username
    account = get_account_for_salesrep(username)
    if account:
        if account.salesrep_set.exists():
            salesrep = account.salesrep_set.latest('created_at')
        
    return salesrep

@schema_context(os.getenv('SCHEMA_NAME'))
def lead_is_for_salesrep(username, salesrep_to_check):
    ret = False
    account_salesrep = get_sales_rep_for_account(username)
    account_sales_rep_igname = account_salesrep.ig_username

    if account_sales_rep_igname == salesrep_to_check:
        ret = True 
    return ret





@schema_context(os.getenv('SCHEMA_NAME'))
def generate_time_slots(start_datetime, end_datetime, interval):
    start = datetime.strptime(start_datetime, "%Y-%m-%d %H:%M")
    end = datetime.strptime(end_datetime, "%Y-%m-%d %H:%M")
    time_slots = []

    while start <= end:
        time_slots.append(start)
        start += timedelta(minutes=interval)

    return time_slots


def get_token():
    try:
        response = requests.post("https://api.thecut.co/v1/auth/token", headers={
            "Authorization": "Basic YzgwMWE2NmEtNDJlMC00ZTZhLThiZTMtOTIwYzExNWY4NWJkOjU1NTM0MTFjLWIxNjMtNDYyNi1iYWU2LTk2YTczMjMzNzMyMQ==",
            "Auth-Client-Version": "1.25.1",
            "Device-Name": "Tm9raWEgQzMy",
            "Installation-Id": "17E229B5-41B7-4F4D-B44A-C76559665E54",
            "Device-Operating-System": "TIRAMISU (33)",
            "Device-Model": "Nokia Nokia C32",
            "Auth-Client-Name": "android-app",
            "Device-Fingerprint": "3a3f05ba6c66de6a",
            "Device-Platform": "android",
            "Signature": "v1 MTcwODMyNTg5NjpKSjltTUVSZjNmMXhtMUNLWHEzOHR1U0RUdDQxQmNpYTo4V09jZTUrS0dNa21ZR0doSGNmbmlxVlR1R0RFbmZIUkRSd1h0RXJua0FzPQ==",
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": "77",
            "Host": "api.thecut.co",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "User-Agent": "okhttp/4.11.0"
        }, json={
            "grant_type": "password",
            "username": "surgbc@gmail.com",
            "password": "ca!kacut"
        })
        data = response.json()
        return data["access_token"]
    except Exception as e:
        print("Error fetching access token:", e)
        raise e

def get_the_cut_info(thecut_username):
    access_token = get_token()
    response = requests.get(f"https://api.thecut.co/v2/barbers/{thecut_username}",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Auth-Client-Version": "1.25.1",
        "Device-Name": "Tm9raWEgQzMy",
        "Installation-Id": "17E229B5-41B7-4F4D-B44A-C76559665E54",
        "Device-Operating-System": "TIRAMISU (33)",
        "Device-Model": "Nokia Nokia C32",
        "Auth-Client-Name": "android-app",
        "Device-Fingerprint": "3a3f05ba6c66de6a",
        "Session-Id": "f822af9b4e3a61e0d5b71eacbca9c5a686fba9d2b968792e729a6138f4fde7e8122528f7230406f75ed335f6b822c732",
        "Device-Platform": "android",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Id": "65d2df444fd2435e639c4b43",
        "Signature": "v1 MTcwODMzNTg5NzprTFVKNmxjNFpiUzU4aXdUTFFsTENWQTFWNUlGSVFLMDpLQlhiand2bVpCeFppZmZieGFtYnd5bzh6aWp3c3FpSUU4ZHd6azViRHRrPQ=="
    })
    return response.json()


def combine_dicts(group):
    combined_dict = {}
    for _, row in group.iterrows():
        combined_dict.update(row.dropna().to_dict())
    return combined_dict


def merge_lists_by_timestamp(dict_list):
    df = pd.DataFrame(dict_list)
    df['created_at'] = pd.to_datetime(df['created_at'])

    # Round the created_at values to the nearest minute
    df['created_at'] = df['created_at'].dt.round('min')
    return df.groupby('created_at').apply(combine_dicts).tolist()



def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if not parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def flatten_dict_list(dict_list, parent_key='', sep='_'):
    items = []
    for d in dict_list:
        if isinstance(d, dict):
            items.extend(flatten_dict(d, parent_key, sep=sep).items())
        else:
            items.append((parent_key, d))
    return dict(items)

def remove_timestamp(dict_):
    if "_created_at" in dict_:
        try:
            del dict_['_created_at']
        except Exception as err:
            print(err)
    return dict_





def initialize_hikerapi_client(is_async=False):
    
    if is_async:
        try:
            client = AsyncClient(
                token=os.getenv('HIKER_API_KEY'),
            )
            return client
        except Exception as e:
            logging.warning("Error initializing Hiker API async client:", e)
            return None
    else:
        try:
            client = Client(
                token=os.getenv('HIKER_API_KEY'),
            )
            return client
        except Exception as e:
            logging.warning("Error initializing Hiker API client:", e)
            return None




def query_gpt(user_input,identifier=None,schema_name=None):
    with schema_context(schema_name):
        # declare chat_session variable
        system_prompt = Prompt.objects.filter(channel='instagram').latest('created_at').text_data
        chat_session= None
        if identifier is not None:
            try:
                # Check if session exists
                conversation_history=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ]
                chat_session = ChatSession.objects.get(identifier=identifier)
                chat_session.conversation_history = conversation_history
                chat_session.save()
                chat_session.add_message("user", user_input)
            except ChatSession.DoesNotExist:
                conversation_history=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input},
                    ]
                chat_session = ChatSession.objects.create(
                    identifier=identifier,
                    conversation_history=conversation_history
                )
        body = {
            "model": "gpt-4-1106-preview",
            "messages": chat_session.conversation_history,
        }
        header = {"Authorization": "Bearer " + os.getenv("OPENAI_API_KEY").strip()}

        res = requests.post("https://api.openai.com/v1/chat/completions", json=body, headers=header)
        # save the response to the database
        gpt_response = res.json()["choices"][0]["message"]["content"]
        chat_session.add_message("system", gpt_response)
        logging.warn(str(["time elapsed", res.elapsed.total_seconds()]))

        return res.json()

def get_access_token():
    return os.getenv("ACCESS_TOKEN")
import time

GRAPH_API_VERSION = "v16.0"   # use the Graph version you target
FB_OAUTH_ENDPOINT = f"https://graph.facebook.com/{GRAPH_API_VERSION}/oauth/access_token"

def exchange_short_for_long(app_id: str, app_secret: str, short_lived_token: str):
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_lived_token
    }
    r = requests.get(FB_OAUTH_ENDPOINT, params=params, timeout=10)
    # r.raise_for_status()
    return r.json()  # contains access_token and expires_in


def exchange_ig_short_for_long(app_id: str, app_secret: str, short_lived_token: str):
    params = {
        "grant_type": "ig_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "access_token": short_lived_token
    }
    r = requests.get(FB_OAUTH_ENDPOINT, params=params, timeout=10)
    # r.raise_for_status()
    return r.json()  # contains access_token and expires_in

def debug_token(input_token: str, app_access_token: str):
    # app_access_token: "<APP_ID>|<APP_SECRET>" or an app token obtained securely
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/debug_token"
    params = {"input_token": input_token, "access_token": app_access_token}
    r = requests.get(url, params=params, timeout=10)
    # r.raise_for_status()
    return r.json()


def validate_or_extend_ig_token(token: str = None):
    debug_response = debug_token(token, f"{os.getenv('FACEBOOK_APP_ID')}|{os.getenv('FACEBOOK_APP_SECRET')}")
    debug_result = debug_response.get('data', {})
    expires_at = debug_result.get("expires_at", 0)
    if expires_at and expires_at < time.time() + 6000:
        print("Token is short being exchanged for a longer-lived token.")
        token_resp = exchange_ig_short_for_long(os.getenv('FACEBOOK_APP_ID'), os.getenv('FACEBOOK_APP_SECRET'), token)
        return token_resp.get('access_token', None)
    else:
        print("Token is valid and does not need extension.")
        return token

def validate_or_extend_token(token: str = None):
    debug_response = debug_token(token, f"{os.getenv('FACEBOOK_APP_ID')}|{os.getenv('FACEBOOK_APP_SECRET')}")
    debug_result = debug_response.get('data', {})
    expires_at = debug_result.get("expires_at", 0)
    if expires_at and expires_at < time.time() + 6000:
        print("Token is short being exchanged for a longer-lived token.")
        token_resp = exchange_short_for_long(os.getenv('FACEBOOK_APP_ID'), os.getenv('FACEBOOK_APP_SECRET'), token)
        return token_resp.get('access_token', None)
    else:
        print("Token is valid and does not need extension.")
        return token
    
