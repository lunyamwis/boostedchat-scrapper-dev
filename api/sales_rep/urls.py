from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SalesRepManager

router = DefaultRouter()
router.register(r"rep", SalesRepManager, basename="rep")


urlpatterns = [
    path("", include(router.urls)),
    path("assign-salesrep/",SalesRepManager.as_view({'post': 'assign_salesrep'}),
        name='assign_salesrep'),
    path("assign-influencer/",SalesRepManager.as_view({'post': 'assign_influencer'}),
        name='assign_influencer')
]
