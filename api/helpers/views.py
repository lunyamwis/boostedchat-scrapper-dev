from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny
from .models import Client, Domain
from .serializers import ClientSerializer, DomainSerializer


class ClientViewSet(ModelViewSet):
    permission_classes = [AllowAny]  # Allow any user (authenticated or not) to access this viewset
    queryset = Client.objects.all()
    serializer_class = ClientSerializer


class DomainViewSet(ModelViewSet):
    permission_classes = [AllowAny]  # Allow any user (authenticated or not) to access this viewset
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer