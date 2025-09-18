# apps/accounts/adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class TenantAwareAdapter(DefaultSocialAccountAdapter):
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
