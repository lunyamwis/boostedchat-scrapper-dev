from django.urls import path
from . import views

urlpatterns = [
    path('webhooks/', views.webhook, name='webhook'),
]
