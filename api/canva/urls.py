# api/canva/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('webhook/', views.canva_webhook, name='canva_webhook'),
    path("sidebar/", views.plugin_sidebar, name="canva_plugin_sidebar"),
    path("execute/", views.execute_automation, name="canva_execute_automation"),

]
