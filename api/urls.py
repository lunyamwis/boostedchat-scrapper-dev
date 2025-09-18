from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.http import HttpResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from allauth.socialaccount.providers.oauth2.views import OAuth2CallbackView
from django.conf.urls.static import static
from . import views

def home(request):
    return HttpResponse("Welcome to the homepage")

urlpatterns = [

    path('admin/', admin.site.urls),  # Admin URL
    # path('', home),  # Root URL
    # path('',include('boostedchatScrapper.urls')),
    path('dj-rest-auth/', include('dj_rest_auth.urls')),
    path('dj-rest-auth/registration/', include('dj_rest_auth.registration.urls')),
    path('instagram/',include('api.instagram.urls')),
    path('whatsapp/',include('api.whatsapp.urls')),
    path('facebook/',include('api.facebookautomator.urls')),
    path('scout/',include('api.scout.urls')),
    path('prompt/',include('api.prompt.urls')),
    path('authentication/',include('api.authentication.urls')),
    path('dialogflow/',include('api.dialogflow.urls')),
    path('sales/',include('api.sales_rep.urls')),
    path('serviceManager/',include('api.serviceManager.urls')),
    path('audittrail/',include('api.audittrails.urls')),
    path('linkedin/',include('api.linkedin.urls')),
    path('gmail/',include('api.gmail.urls')),
    path('analyst/',include('api.analyst.urls')),
    path('workflow/',include('api.workflow.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('accounts/', include('allauth.urls')),  # Allauth URLs
    path('helpers/', include('api.helpers.urls')),  # Include the URLs from the helpers app
    path('', include('home.urls')),  # Include the URLs from the home app
    path('billing/', include('billing.urls')),  # Include the URLs from the billing app
    # path("oauth/callback/<str:provider>/", views.oauth_callback, name="oauth_callback"),
    path("oauth/callback/<str:provider>/", views.TenantOAuth2CallbackView(), name="oauth_callback"),
    # path('accounts/<str:provider>/login/callback/', views.oauth_callback2, name='socialaccount_callback_custom'),
    path('accounts/<str:provider>/login/callback/2', OAuth2CallbackView, name='socialaccount_callback_custom'),
    
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


handler404 = "api.views.handler404"
handler403 = "api.views.handler403"
handler400 = "api.views.handler400"
handler500 = "api.views.handler500"
