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
import logging
from django.views import View
from django.shortcuts import redirect
from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.helpers import complete_social_login, render_authentication_error
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from django.core.exceptions import PermissionDenied
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

class TenantOAuth2CallbackView(View):
    """
    Simple multitenant OAuth2 callback view for django-allauth 0.61.1
    """

    def get(self, request, *args, **kwargs):
        provider_name = kwargs.get("provider")
        adapter = get_adapter(request)
        provider = adapter.get_provider(provider_name)

        # Grab 'state', 'code', 'error' directly from GET params
        state_id = request.GET.get("state")
        code = request.GET.get("code")
        error = request.GET.get("error")

        if error or not code:
            logger.warning(f"OAuth2 error from {provider_name}: {error}")
            return render_authentication_error(
                request,
                provider,
                error=None,
                extra_context={"callback_view": self, "state_id": state_id},
            )

        # Restore state from session
        state = adapter.unstash_state(request, state_id)

        if state is None:
            logger.error(f"Could not restore state for {provider_name}")
            return render_authentication_error(
                request,
                provider,
                extra_context={"callback_view": self, "state_id": state_id},
            )

        # Exchange code for token
        app = provider.get_app(request)
        client = adapter.get_client(request, app)

        try:
            access_token_data = adapter.get_access_token_data(
                request,
                app,
                client,
                pkce_code_verifier=state.get("pkce_code_verifier"),
            )
            token = adapter.parse_token(access_token_data)
            if app.pk:
                token.app = app

            login = adapter.complete_login(
                request, app, token, response=access_token_data
            )
            login.token = token
            login.state = state

            # Optional: store tenant in session for redirect
            tenant = state.get("tenant")
            if tenant:
                request.session["tenant"] = tenant
                logger.info(f"OAuth2 login successful for tenant: {tenant}")

            return complete_social_login(request, login)

        except (PermissionDenied, OAuth2Error, RequestException) as e:
            logger.error(f"OAuth2 token exchange failed for {provider_name}: {e}")
            return render_authentication_error(
                request,
                provider,
                exception=e,
                extra_context={"callback_view": self, "state": state},
            )

def oauth_callback2(request, provider):
    query_string = request.META.get("QUERY_STRING", "")
    logger.debug("[CALLBACK] Provider=%s Raw query=%s", provider, query_string)
    # Replace state in query string with the original Allauth state
    query_params = request.GET.copy()
    
    

    forward_url = f"https://lunyamwi.org/accounts/{provider}/login/callback/2?{query_params.urlencode()}"

    logger.debug("[CALLBACK] Forwarding to %s", forward_url)

    return redirect(forward_url)




