from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('debug-request/', views.debug_request, name='debug-request'),
]
