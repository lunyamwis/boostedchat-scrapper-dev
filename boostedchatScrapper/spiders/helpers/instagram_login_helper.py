import email
import imaplib
import logging
import os
import random
import requests
import backoff
import re
import time
from pathlib import Path

from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from instagrapi import Client
from instagrapi.mixins.challenge import ChallengeChoice
from django_tenants.utils import schema_context
from api.scout.models import Scout,Device

logger = logging.getLogger()


@schema_context(os.getenv("SCHEMA_NAME"))
@backoff.on_exception(
    backoff.constant,  # Use constant backoff strategy
    Exception,  # Retry on any exception
    interval=70,  # Wait 60 seconds between retries
    max_tries=5  # Retry up to 5 times
)
def change_password_handler_(username):
    try:
        subject = 'Login Failure'
        message = f'Scout {username} failed to login after 3 attempts with error: update your password'
        from_email = 'lutherlunyamwi@gmail.com'
        scout = Scout.objects.filter(username=username).latest('created_at')
        recipient_list = [scout.email,scout.master.email]
        send_mail(subject, message, from_email, recipient_list)
    except Exception as error:
        logging.warning(error)
    try:
        scout = Scout.objects.filter(username=username).latest('created_at')
        password_update = scout.password_update
        logging.warning("Password update: %s", password_update)
        if password_update is None:
            scout.available = False
            scout.save()
            raise ValueError("Password update is None")
        return password_update
    except ObjectDoesNotExist:
        raise ValueError("Scout object does not exist")

        

@schema_context(os.getenv("SCHEMA_NAME"))
@backoff.on_exception(
    backoff.constant,  # Use constant backoff strategy
    Exception,  # Retry on any exception
    interval=70,  # Wait 60 seconds between retries
    max_tries=5  # Retry up to 5 times
)
def challenge_code_handler_(username):
    try:
        subject = 'Login Failure'
        message = f'Scout {username} failed to login after 3 attempts with error: key in the login code'
        from_email = 'lutherlunyamwi@gmail.com'
        scout = Scout.objects.filter(username=username).latest('created_at')
        recipient_list = [scout.email,scout.master.email]
        send_mail(subject, message, from_email, recipient_list)
    except Exception as error:
        logging.warning(error)
    try:
        scout = Scout.objects.filter(username=username).latest('created_at')
        login_code = scout.login_code
        logging.warning("Login code: %s", login_code)
        if login_code is None:
            scout.available = False
            scout.save()
            raise ValueError("Login code is None")
        return str(login_code)
    except ObjectDoesNotExist:
        raise ValueError("Scout object does not exist")

def get_code_from_email(username):
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(os.getenv("CHALLENGE_EMAIL"), os.getenv("CHALLENGE_PASSWORD"))
    mail.select("inbox")
    result, data = mail.search(None, "(UNSEEN)")
    assert result == "OK", "Error1 during get_code_from_email: %s" % result
    ids = data.pop().split()
    for num in reversed(ids):
        mail.store(num, "+FLAGS", "\\Seen")  # mark as read
        result, data = mail.fetch(num, "(RFC822)")
        assert result == "OK", "Error2 during get_code_from_email: %s" % result
        msg = email.message_from_string(data[0][1].decode())
        payloads = msg.get_payload()
        if not isinstance(payloads, list):
            payloads = [msg]
        code = None
        for payload in payloads:
            body = payload.get_payload(decode=True).decode()
            if "<div" not in body:
                continue
            match = re.search(">([^>]*?({u})[^<]*?)<".format(u=username), body)
            if not match:
                continue
            print("Match from email:", match.group(1))
            match = re.search(r">(\d{6})<", body)
            if not match:
                print('Skip this email, "code" not found')
                continue
            code = match.group(1)
            if code:
                return code
    return False




@schema_context(os.getenv("SCHEMA_NAME"))
def login_user(scout: Scout):

    """
    Attempts to login to Instagram using either the provided session information
    or the provided username and password.
    """
    
    cl = Client()
    
    device = Device.objects.filter(scout=scout).latest('created_at')
    scout = Scout.objects.get(id=device.scout_id)
    if device.status==0 or device.status == 1: 
        cl.set_device(device={
                "app_version": device.app_version,
                "android_version": device.android_version,
                "android_release": device.android_release,
                "dpi": device.dpi,
                "resolution": device.resolution,
                "manufacturer": device.manufacturer,
                "device": device.device,
                "model": device.model,
                "cpu": device.cpu,
                "version_code": device.version_code,
            },reset=True)
        cl.set_user_agent(f"Instagram {device.app_version} Android ({device.android_version}/{device.android_release}; {device.dpi}; {device.resolution}; {device.manufacturer}; {device.device}; {device.model}; {device.cpu}; en_US; {device.version_code})",reset=True)
        cl.set_country(scout.country)
        cl.set_country_code(scout.code)

    # cl.challenge_code_handler = challenge_code_handler(scout.username)
    # cl.change_password_handler = change_password_handler(scout.username)
    # cl.login_by_sessionid()
    # index = 1
    # before_ip = cl._send_public_request("https://api.ipify.org/")
    
    username = f"user-{os.getenv('PROXY_USERNAME').strip()}-country-{str.lower(scout.country)}-city-{str.lower(scout.city)}"
    password = os.getenv('PROXY_PASSWORD').strip()
    proxy = None
    
    proxy = f"http://{username}:{password}@gate.decodo.com:10001"

    
    cl.set_proxy(
        proxy
    )
    # after_ip = cl._send_public_request("https://api.ipify.org/")
    # print(f"Before: {before_ip}")
    # print(f"After: {after_ip}")
    # cl.challenge_code_handler = challenge_code_handler(scout.username, 1)
    cl.delay_range = [5, 8]
    max_attempts = 2
    session_file_path = Path(f"{scout.username}.json")
    if os.path.exists(session_file_path):
        for attempt in range(1, max_attempts + 1):
            session = cl.load_settings(session_file_path)
            if session:
                cl.set_settings(session)
                try:
                    cl.get_timeline_feed()  # Check if the session is valid
                    print("Session is valid, login with session")

                    break
                except Exception as e:
                    old_session = cl.get_settings()
                    cl.set_settings({})
                    cl.set_uuids(old_session["uuids"])
                    print(f"Session is invalid (attempt {attempt}): {e}")
                    if attempt < max_attempts:
                        print(f"Waiting 1 minute before trying again (attempt {attempt})")
                        time.sleep(60)  # Wait for 1 minute
                    else:
                        print("All attempts failed, removing session file and logging in with username and password")
                        os.remove(session_file_path)
                        logging.warning("Error during login:")
                        try:
                            subject = 'Login Failure'
                            message = f'Scout {scout.username} failed to login after 3 attempts with error:'
                            from_email = 'lutherlunyamwi@gmail.com'
                            recipient_list = [scout.email,scout.master.email]
                            send_mail(subject, message, from_email, recipient_list)
                        except Exception as error:
                            print(error)
                        cl.login(username=scout.username,password=scout.password)
                        cl.dump_settings(session_file_path)
                        device.status = 1
                        device.save()
                        print("Session saved to file")

    else:
        
        try:
            subject = 'Login Failure'
            message = f'Scout {scout.username} failed to login after 3 attempts with error:'
            from_email = 'lutherlunyamwi@gmail.com'
            recipient_list = [scout.email,scout.master.email]
            send_mail(subject, message, from_email, recipient_list)
        except Exception as error:
            print(error)
        cl.login(username=scout.username,password=scout.password)
        print("Login with username and password")
        cl.dump_settings(session_file_path)
        device.status = 1
        device.save()
        print("Session saved to file")
        

    return cl
