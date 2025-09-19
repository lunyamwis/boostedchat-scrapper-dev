# yourapp/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .utils import decode_state

import logging

logger = logging.getLogger(__name__)

def handler404(request, exception):
    exc_str = str(exception)
    logger.error("404 at %s: %s", request.path, exc_str)
    messages.error(request, f"⚠️ Page not found")
    return render(request, "errors/404.html", status=404)

def handler403(request, exception):
    exc_str = str(exception)
    logger.error("403 at %s: %s", request.path, exc_str)
    messages.error(request, f"⚠️ Forbidden")
    return render(request, "errors/403.html", status=403)

def handler400(request, exception):
    exc_str = str(exception)
    logger.error("400 at %s: %s", request.path, exc_str)
    messages.error(request, f"⚠️ Bad request")
    return render(request, "errors/400.html", status=400)

def handler500(request):
    # Generic 500 page for user
    messages.error(request, "⚠️ Something went wrong on our side. Please try again later.")
    return render(request, "errors/500.html", status=500)

# views.py



def oauth_callback(request, provider):
    query_string = request.META.get("QUERY_STRING", "")
    logger.debug("[CALLBACK] Provider=%s Raw query=%s", provider, query_string)
    # Replace state in query string with the original Allauth state
    query_params = request.GET.copy()
    
    

    forward_url = f"https://lunyamwi.org/accounts/{provider}/login/callback/?{query_params.urlencode()}"

    logger.debug("[CALLBACK] Forwarding to %s", forward_url)

    return redirect(forward_url)
# myapp/views.py
# myapp/views.py
# myapp/views.py
# myapp/views.py
import logging
from django.views import View
from django.shortcuts import redirect
from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.helpers import complete_social_login, render_authentication_error
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from django.core.exceptions import PermissionDenied
from requests.exceptions import RequestException
from api.authentication.models import Token,User
from allauth.socialaccount.providers.base import AuthError
from django.contrib.auth import get_user_model, authenticate, login
from urllib.parse import unquote
import os
import requests
from rest_framework.response import Response
from rest_framework import status



logger = logging.getLogger(__name__)

class TenantOAuth2CallbackView(View):
    """
    Django CBV for multitenant OAuth2 callback (Allauth 0.61.1)
    """

    def get(self, request, *args, **kwargs):
        provider_name = kwargs.get("provider")
        if provider_name == "google":
            code = unquote(request.GET.get("code", ""))
            redirect_uri = "https://lunyamwi.org/oauth/callback/google/"
            client_id = os.getenv("GMAIL_CLIENT_ID", "")
            client_secret = os.getenv("GMAIL_CLIENT_SECRET", "")
            
            if not code:
                raise PermissionDenied("Missing authorization code")
            
            if not client_id or not client_secret:
                raise PermissionDenied("GMAIL_CLIENT_ID or GMAIL_CLIENT_SECRET not configured")
            
            token_url = "https://oauth2.googleapis.com/token"
            data = {
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            }
            
            response = requests.post(token_url, data=data)
            if response.status_code != 200:
                raise PermissionDenied("Failed to exchange code for tokens")

            if response.status_code == 200:
                tokens = response.json()
                logger.debug("[CALLBACK] Tokens received: %s", tokens)
                try:
                    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
                    resp = requests.get("https://www.googleapis.com/oauth2/v2/userinfo", headers=headers)
                    user_info = resp.json()
                    email = user_info.get("email")
                    logger.debug("[CALLBACK] User info: %s", user_info)
                    
                except RequestException as e:
                    print("Failed to fetch user info: %s", e)
                try:
                    # Save tokens to the database
                    user = User.objects.get(email=email)
                    # login(request, user)
                    Token.objects.update_or_create(
                        user=user,
                        provider=provider_name,
                        access_token=tokens.get("access_token"),
                        refresh_token=tokens.get("refresh_token"),
                        token_type=tokens.get("token_type", "refresh")
                    )
                except Exception as e:
                    logger.warning("Error saving tokens: %s", e)
                tenant_name = user.client_set.last().name
                # user = authenticate(request, username=user.username, password=user.password)
                # if user:
                    # login(request, user)
                try:
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                except Exception as e:
                    logger.warning("Error logging in user: %s", e)
                return redirect(f"https://{tenant_name}.lunyamwi.org/workflow/")
            
            return redirect("/")
        elif provider_name == "facebook":
            code = unquote(request.GET.get("code", ""))
            redirect_uri = "https://lunyamwi.org/oauth/callback/facebook/"
            client_id = os.getenv("FACEBOOK_APP_ID", "")
            client_secret = os.getenv("FACEBOOK_APP_SECRET", "")
            if not code:
                raise PermissionDenied("Missing authorization code")
            if not client_id or not client_secret:
                raise PermissionDenied("FACEBOOK_APP_ID or FACEBOOK_APP_SECRET not configured")
            token_url = (
                f"https://graph.facebook.com/v12.0/oauth/access_token?"
                f"client_id={os.getenv('FACEBOOK_APP_ID')}"
                f"&redirect_uri={redirect_uri}"
                f"&client_secret={os.getenv('FACEBOOK_APP_SECRET')}"
                f"&code={code}"
            )
            token_response = requests.get(token_url)
            token_data = token_response.json()
            print("Token data:", token_data)
            access_token = token_data.get("access_token")

            if not access_token:
                raise PermissionDenied("Failed to get access token", token_data)

            # Get user profile info
            profile_url = (
                f"https://graph.facebook.com/me?"
                f"fields=id,name,email"
                f"&access_token={access_token}"
            )
            profile_response = requests.get(profile_url)
            profile_data = profile_response.json()
            try:
                email = profile_data.get("email")
                user = User.objects.get(email=email)
                # login(request, user)
                Token.objects.update_or_create(
                    user=user,
                    provider=provider_name,
                    access_token=access_token,
                    token_type="refresh"
                )
            except Exception as e:
                logger.warning("Error saving Facebook tokens: %s", e)


            tenant_name = user.client_set.last().name
            # user = authenticate(request, username=user.username, password=user.password)
            # if user:
            # try:
            #     login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            # except Exception as e:
            #     logger.warning("Error logging in user: %s", e)
            # return redirect(f"https://{tenant_name}.lunyamwi.org/workflow/")
            return redirect("tenant_redirect")
            # return redirect("/")


from django.contrib.auth import login
from django.shortcuts import redirect
import logging

logger = logging.getLogger(__name__)

def tenant_login_and_redirect(request, user):
    """
    Call this after you have the `user` instance (e.g. after oauth or lookup).
    """
    # sanity checks trying to force user to login checked
    # login (must provide backend if you didn't call authenticate())
    try:
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    except Exception as e:
        logger.exception("login failed: %s", e)
        return redirect("/login/?error=login_failed")

    # force session persistence (helps ensure Set-Cookie is emitted)
    try:
        request.session.save()
    except Exception:
        # session save might be redundant but safe
        logger.exception("session save failed")

    # build tenant host safely
    tenant_obj = user.client_set.last()
    if not tenant_obj:
        return redirect("/")

    tenant_name = tenant_obj.name.strip().lower()
    # sanitize tenant_name to avoid injection; ensure allowed characters only
    # e.g. tenant_name = re.sub(r'[^a-z0-9-]', '', tenant_name)

    redirect_url = f"https://{tenant_name}.lunyamwi.org/workflow/"
    response = redirect(redirect_url)
    return response

def oauth_callback2(request, provider):
    query_string = request.META.get("QUERY_STRING", "")
    logger.debug("[CALLBACK] Provider=%s Raw query=%s", provider, query_string)
    # Replace state in query string with the original Allauth state
    query_params = request.GET.copy()
    
    

    forward_url = f"https://lunyamwi.org/accounts/{provider}/login/callback/2?{query_params.urlencode()}"

    logger.debug("[CALLBACK] Forwarding to %s", forward_url)

    return redirect(forward_url)





