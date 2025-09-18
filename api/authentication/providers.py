from allauth.socialaccount.providers.google.provider import GoogleProvider
from allauth.socialaccount.providers.facebook.provider import FacebookProvider
from allauth.socialaccount.providers import registry

class TenantAwareGoogleProvider(GoogleProvider):

    def get_auth_params(self, request, action):
        params = super().get_auth_params(request, action)
        tenant = getattr(request.tenant, "schema_name", "public")
        params["tenant"] = tenant
        print(params)
        return params

class TenantAwareFacebookProvider(FacebookProvider):

    def get_auth_params(self, request, action):
        params = super().get_auth_params(request, action)
        tenant = getattr(request.tenant, "schema_name", "public")
        params["tenant"] = tenant
        print(params)
        return params
