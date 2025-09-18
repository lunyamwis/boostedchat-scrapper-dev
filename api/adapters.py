# apps/accounts/adapters.py
import logging
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

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
        return super().authentication_error(request, provider_id, error, exception, extra_context)

    def populate_state(self, request, state):
        """Inject tenant info into the OAuth state param before redirecting to provider."""
        tenant = getattr(request, "tenant", None)  # django-tenants gives this
        if tenant:
            state["tenant"] = tenant.schema_name  # or tenant.domain_url
        return super().populate_state(request, state)

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
