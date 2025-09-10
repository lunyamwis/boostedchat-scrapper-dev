from rest_framework import serializers
from .models import Client, Domain

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['name']

class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ['domain', 'tenant']