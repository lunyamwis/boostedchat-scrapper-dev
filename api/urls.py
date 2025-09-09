from django.contrib import admin
from django.urls import path,include
from django.http import HttpResponse

def home(request):
    return HttpResponse("Welcome to the homepage")

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin URL
    # path('', home),  # Root URL
    # path('',include('boostedchatScrapper.urls')),
    path('instagram/',include('api.instagram.urls')),
    path('whatsapp/',include('api.whatsapp.urls')),
    path('facebook/',include('api.facebook.urls')),
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
    path('',include('api.workflow.urls')),
]
