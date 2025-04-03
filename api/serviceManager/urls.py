# dockerapp/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('restart-container/', views.RestartContainerView.as_view(), name='restart-container'),  # Removed <str:container_name>
    path('reset-conversations/', views.ResetConversationsView.as_view(), name='reset-conversations'),
    path('force-recreate/', views.ForceRecreateApi.as_view(), name='force-recreate'),
]