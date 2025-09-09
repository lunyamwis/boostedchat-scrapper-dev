from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/",views.dashboard_two,name="dashboard"),
    path("query_generator/",views.dashboard,name="query_generator"),
    path('api/dashboard/', views.dashboard_api, name='dashboard_api'),
    path('api/get_sql/<str:pk>/', views.get_sql_record, name='get_sql_record'),
    path('api/get_sql_records/', views.get_sql_records, name='get_sql_records'),
]