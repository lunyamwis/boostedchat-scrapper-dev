# apps/accounts/adapters.py
import logging
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.http import HttpResponse
from .utils import encode_state

logger = logging.getLogger(__name__)

class TenantAwareAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Called after successful authentication, but before login.
        Great place to debug and inspect the flow.
        """
        logger.debug("Pre social login triggered")
        logger.debug("SocialLogin object: %s", sociallogin)
        logger.debug("Provider: %s", sociallogin.account.provider)
        logger.debug("User email: %s", sociallogin.user.email)

    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """
        Called if there's an error in the social login flow.
        """
        logger.error("Authentication error for provider %s", provider_id)
        logger.error("Error: %s", error)
        logger.error("Exception: %s", exception)
        logger.error("Extra context: %s", extra_context)
        return HttpResponse(
            f"Authentication error for {provider_id}: {error} ({exception})",
            status=400
        )

    
    def get_connect_redirect_url(self, request, socialaccount):
        return super().get_connect_redirect_url(request, socialaccount)
    
    
    
    def generate_state_param(self, state_dict: dict) -> str:
        # First let allauth generate the base state string
        base_state = super().generate_state_param(state_dict)
        
        print(state_dict)
        # Extract tenant from state_dict (must be injected earlier!)
        tenant_name = state_dict.get("tenant", "public")

        encoded = encode_state(tenant_name, base_state)
        logger.debug(
            "[ADAPTER] generate_state_param tenant=%s base_state=%s encoded=%s",
            tenant_name, base_state, encoded
        )
        return encoded
    
    

    def get_login_redirect_url(self, request):
        """After successful login, send user back to the correct tenant subdomain."""
        # Allauth will decode the state back into request.GET["state"]
        tenant = None

        # Try to recover tenant info from state/session
        if "state" in request.GET:
            try:
                import json
                from allauth.socialaccount.helpers import get_request_param

                state_param = get_request_param(request, "state")
                state_data = json.loads(state_param)
                tenant = state_data.get("tenant")
            except Exception:
                pass

        # Fallback to django-tenants request.tenant
        if not tenant and hasattr(request, "tenant"):
            tenant = request.tenant.schema_name

        if tenant:
            return f"https://{tenant}.lunyamwi.org/workflow/"
        return "/"  # fallback if tenant missing
