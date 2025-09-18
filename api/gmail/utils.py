import requests

import urllib.parse
import secrets
from urllib.parse import unquote, urlparse, parse_qs
import logging
import re
from django_tenants.utils import schema_context
import os
from api.gmail.models import ChatSession
from api.prompt.models import Prompt


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_google_oauth_url(client_id, redirect_uri):
    base_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    scopes = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.modify",
        "openid"
    ]
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "state": secrets.token_urlsafe(16),
        "access_type": "offline",
        "prompt": "consent"
    }
    url = f"{base_auth_url}?{urllib.parse.urlencode(params)}"
    return url

def exchange_code_for_tokens(client_id, client_secret, code, redirect_uri):
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    response = requests.post(token_url, data=data)
    response_data = response.json()
    return response_data


def extract_code_from_url(callback_url):
    """
    Extract authorization code from OAuth callback URL
    Handles various URL formats and parameters
    """
    try:
        # Parse the URL
        parsed_url = urlparse(callback_url)
        
        # Extract query parameters
        query_params = parse_qs(parsed_url.query)
        
        # Look for 'code' parameter
        if 'code' in query_params:
            code = query_params['code'][0]
            logger.info(f"Extracted code from URL: {code[:20]}...")
            return code
        
        # Alternative: try to extract code using regex if URL parsing fails
        code_match = re.search(r'code=([^&]+)', callback_url)
        if code_match:
            code = code_match.group(1)
            # URL decode if necessary
            code = unquote(code)
            logger.info(f"Extracted code using regex: {code[:20]}...")
            return code
        
        # Check for error in callback URL
        if 'error' in query_params:
            error = query_params['error'][0]
            error_description = query_params.get('error_description', ['Unknown error'])[0]
            raise Exception(f"OAuth error: {error} - {error_description}")
        
        raise Exception("No authorization code found in callback URL")
        
    except Exception as e:
        logger.error(f"Error extracting code from URL: {str(e)}")
        raise




@schema_context(os.getenv('SCHEMA_NAME'))
def query_gpt(user_input,identifier=None):
    # declare chat_session variable
    system_prompt = Prompt.objects.filter(channel='gmail').latest('created_at').text_data
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
