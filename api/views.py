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
import logging
from django.views import View
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from requests.exceptions import RequestException

from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.helpers import complete_social_login, render_authentication_error, get_request_param
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from allauth.socialaccount.providers.base import AuthError

logger = logging.getLogger(__name__)

class TenantOAuth2CallbackView(View):
    """
    Django CBV for handling OAuth2 callbacks.
    """

    def get(self, request, *args, **kwargs):
        self.adapter = get_adapter(request)
        provider = self.adapter.get_provider()

        # Unstash state from session
        state = None
        state_id = get_request_param(request, "state")
        if state_id:
            state = self.adapter.unstash_state(request, state_id)

        if state is None:
            return render_authentication_error(
                request,
                provider,
                extra_context={"state_id": state_id, "callback_view": self},
            )

        # Error from provider?
        if "error" in request.GET or "code" not in request.GET:
            auth_error = request.GET.get("error")
            error = (
                AuthError.CANCELLED
                if auth_error == getattr(self.adapter, "login_cancelled_error", None)
                else AuthError.UNKNOWN
            )
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
                request,
                app,
                client,
                pkce_code_verifier=state.get("pkce_code_verifier"),
            )
            token = self.adapter.parse_token(access_token_data)
            if app.pk:
                token.app = app

            login = self.adapter.complete_login(
                request, app, token, response=access_token_data
            )
            login.token = token
            login.state = state

            return complete_social_login(request, login)

        except (PermissionDenied, OAuth2Error, RequestException) as e:
            return render_authentication_error(
                request, provider, exception=e, extra_context={"state": state}
            )




def oauth_callback2(request, provider):
    query_string = request.META.get("QUERY_STRING", "")
    logger.debug("[CALLBACK] Provider=%s Raw query=%s", provider, query_string)
    # Replace state in query string with the original Allauth state
    query_params = request.GET.copy()
    
    

    forward_url = f"https://lunyamwi.org/accounts/{provider}/login/callback/2?{query_params.urlencode()}"

    logger.debug("[CALLBACK] Forwarding to %s", forward_url)

    return redirect(forward_url)




