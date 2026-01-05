from django.urls import path
from .views  import dashboard, airbnb_dashboard

urlpatterns = [
    path("dashboard/<int:room_id>/", dashboard, name="dashboard"),
    path("airbnb/dashboard/<int:listing_id>/", airbnb_dashboard, name="airbnb_dashboard"),
]
