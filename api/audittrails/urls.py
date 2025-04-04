from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"entries", views.LogEntryViewset, basename="entries")

urlpatterns = [
    path('filter-by-status/<account_id>/', views.status_log_entries_by_account )
]

urlpatterns += router.urls
