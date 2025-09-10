from django.urls import path,include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'clients', views.ClientViewSet, basename='client')
router.register(r'domains', views.DomainViewSet, basename='domain')

urlpatterns = [
    path('', include(router.urls)),
]