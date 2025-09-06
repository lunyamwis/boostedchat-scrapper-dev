import requests

import urllib.parse
import secrets
from urllib.parse import unquote


def get_google_oauth_url(client_id, redirect_uri):
    base_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    scopes = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid"
    ]
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "state": secrets.token_urlsafe(16),  # CSRF protection token
        "access_type": "offline",  # to get refresh token
        "prompt": "consent"  # force consent screen
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



def decode_url(encoded_str):
    return unquote(encoded_str)
