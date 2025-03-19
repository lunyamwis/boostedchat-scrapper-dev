from django.urls import path
from . import views

urlpatterns = [
    path("",views.dashboard_two,name="dashboard"),
    path("query_generator/",views.dashboard,name="query_generator"),
    path('api/dashboard/', views.dashboard_api, name='dashboard_api'),
]