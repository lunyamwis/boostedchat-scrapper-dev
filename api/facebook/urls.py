from django.urls import path
from . import views

urlpatterns = [
    path('webhook/', views.webhook, name='webhook'),
    path('scrap_facebook_group_members/', views.scrap_facebook_group_members_view, name='scrap_facebook_group_members'),
    path('send_first_message/', views.send_first_message_view, name='send_first_message'),
    path('scrap_facebook_group_members_api/', views.scrap_facebook_group_members_api, name='scrap_facebook_group_members_api'),
    path('send_first_message_api/', views.send_first_message_api, name='send_first_message_api'),
]
