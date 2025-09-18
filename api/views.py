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

import logging
from allauth.socialaccount.providers.oauth2.views import OAuth2CallbackView

class TenantOAuth2CallbackView(OAuth2CallbackView):
    def __call__(self, request, *args, **kwargs):
        print("Callback hit:", request.GET)
        return super().__call__(request, *args, **kwargs)



def oauth_callback2(request, provider):
    query_string = request.META.get("QUERY_STRING", "")
    logger.debug("[CALLBACK] Provider=%s Raw query=%s", provider, query_string)
    # Replace state in query string with the original Allauth state
    query_params = request.GET.copy()
    
    

    forward_url = f"https://lunyamwi.org/accounts/{provider}/login/callback/2?{query_params.urlencode()}"

    logger.debug("[CALLBACK] Forwarding to %s", forward_url)

    return redirect(forward_url)




