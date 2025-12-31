from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('shop/',views.shop, name='shop'),
    path('debug-request/', views.debug_request, name='debug-request'),
    path('privacy-gmail/', views.privacy_gmail, name='privacy-gmail')
]
