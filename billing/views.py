from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
# Create your views here.

class PaystackWebhookView(APIView):
    def post(self, request, *args, **kwargs):
        # Handle the webhook payload
        payload = request.data
        # Process the payload as needed
        print("Received Paystack webhook:", payload)
        return Response({"status": "success"}, status=200)