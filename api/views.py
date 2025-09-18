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
import logging
from django.views import View
from django.shortcuts import redirect, render
from django.conf import settings
from django.core.exceptions import PermissionDenied
from requests.exceptions import RequestException
from allauth.socialaccount.helpers import complete_social_login, render_authentication_error
from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount import state as statekit
from allauth.socialaccount.helpers import get_request_param, add_query_params
from allauth.socialaccount import app_settings as account_settings

logger = logging.getLogger(__name__)

class TenantOAuth2CallbackView(View):
    """
    Django CBV for multitenant OAuth2 callback.
    All logic is in the GET method.
    """

    def get(self, request, *args, **kwargs):
        # Get provider
        self.adapter = get_adapter(request)
        provider = self.adapter.get_provider()

        # Decode state
        state, resp = self._get_state(request, provider)
        if resp:
            return resp

        # Handle errors or missing code
        if "error" in request.GET or "code" not in request.GET:
            auth_error = request.GET.get("error")
            from allauth.socialaccount.providers.base import AuthError
            if auth_error == getattr(self.adapter, "login_cancelled_error", None):
                error = AuthError.CANCELLED
            else:
                error = AuthError.UNKNOWN
            logger.warning("OAuth2 login error: %s", auth_error)
            return render_authentication_error(
                request,
                provider,
                error=error,
                extra_context={"state": state, "callback_view": self},
            )

        # Exchange code for token
        app = provider.get_app(request)
        client = self.adapter.get_client(request, app)
        try:
            access_token_data = self.adapter.get_access_token_data(
                request, app, client, pkce_code_verifier=state.get("pkce_code_verifier")
            )
            token = self.adapter.parse_token(access_token_data)
            if app.pk:
                token.app = app

            login: SocialLogin = self.adapter.complete_login(
                request, app, token, response=access_token_data
            )
            login.token = token
            login.state = state

            # Log tenant
            tenant = state.get("tenant")
            logger.info("OAuth2 login successful for tenant: %s", tenant)
            if tenant:
                request.session["tenant"] = tenant

            return complete_social_login(request, login)

        except (PermissionDenied, OAuth2Error, RequestException) as e:
            logger.error("OAuth2 token exchange error: %s", e)
            return render_authentication_error(
                request, provider, exception=e, extra_context={"state": state}
            )

    def _get_state(self, request, provider):
        state = None
        state_id = get_request_param(request, "state")
        if self.adapter.supports_state and state_id:
            state = statekit.unstash_state(request, state_id)
        else:
            state = statekit.unstash_last_state(request)

        if state is None:
            resp = self._redirect_strict_samesite(request, provider)
            if resp:
                return None, resp
            return None, render_authentication_error(
                request,
                provider,
                extra_context={"state_id": state_id, "callback_view": self},
            )
        return state, None

    def _redirect_strict_samesite(self, request, provider):
        if "_redir" in request.GET or settings.SESSION_COOKIE_SAMESITE.lower() != "strict" or request.method != "GET":
            return
        redirect_to = request.get_full_path()
        redirect_to = add_query_params(redirect_to, {"_redir": ""})
        return render(
            request,
            "socialaccount/login_redirect." + account_settings.TEMPLATE_EXTENSION,
            {"provider": provider, "redirect_to": redirect_to},
        )




def oauth_callback2(request, provider):
    query_string = request.META.get("QUERY_STRING", "")
    logger.debug("[CALLBACK] Provider=%s Raw query=%s", provider, query_string)
    # Replace state in query string with the original Allauth state
    query_params = request.GET.copy()
    
    

    forward_url = f"https://lunyamwi.org/accounts/{provider}/login/callback/2?{query_params.urlencode()}"

    logger.debug("[CALLBACK] Forwarding to %s", forward_url)

    return redirect(forward_url)




