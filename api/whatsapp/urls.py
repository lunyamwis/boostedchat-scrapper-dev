from django.urls import path
from . import views

urlpatterns = [
    path('create-flow/', views.CreateFlowView.as_view(), name='create_flow'),
    path('webhook/', views.webhook, name='webhook'),
    path('send-message/',views.SendBatchWhatsAppView.as_view(), name='send_message'),
    # path('webhook/survey/',views.WebhookView.as_view(), name='webhook_survey'),
]
