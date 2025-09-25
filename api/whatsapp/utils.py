from django_tenants.utils import schema_context
import os
import requests
import logging
import time
from api.whatsapp.models import ChatSession
from api.prompt.models import Prompt
GRAPH_API_VERSION = "v16.0"   # use the Graph version you target
FB_OAUTH_ENDPOINT = f"https://graph.facebook.com/{GRAPH_API_VERSION}/oauth/access_token"

def query_gpt(prompt,phone_number=None, schema_name=None):
    # declare chat_session variable
    with schema_context(schema_name):
        system_prompt = Prompt.objects.filter(channel='whatsapp').latest('created_at').text_data
        chat_session= None
        if phone_number is not None:
            try:
                # Check if session exists
                chat_session = ChatSession.objects.get(phone=phone_number)
                chat_session.add_message("user", prompt)
            except ChatSession.DoesNotExist:
                conversation_history=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ]
                chat_session = ChatSession.objects.create(
                    phone_number=phone_number,
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

        return gpt_response

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

def debug_token(input_token: str, app_access_token: str):
    # app_access_token: "<APP_ID>|<APP_SECRET>" or an app token obtained securely
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/debug_token"
    params = {"input_token": input_token, "access_token": app_access_token}
    r = requests.get(url, params=params, timeout=10)
    # r.raise_for_status()
    return r.json()


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
    
