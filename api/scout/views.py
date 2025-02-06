import os
from django.shortcuts import render

# Create your views here.
from .models import Scout,Device
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_tenants.utils import schema_context
from boostedchatScrapper.spiders.helpers.instagram_login_helper import login_user

class TestAccount(APIView):
    def post(self, request):
        with schema_context(os.getenv("SCHEMA_NAME")):
            scouts = Scout.objects.all()
            for scout in scouts:
                try:
                    client = login_user(scout)
                    scout.available = True
                    scout.save()
                except Exception as e:
                    print(e)
                    scout.available = False
                    scout.save()    
        return Response({"success":True},status=status.HTTP_200_OK)
        
