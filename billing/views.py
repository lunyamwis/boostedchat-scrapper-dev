from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from api.helpers.models import Client, Domain

from django_tenants.utils import schema_context
from django.utils import timezone
from django.core.mail import send_mail
# Create your views here.

class PaystackWebhookView(APIView):
    permission_classes = [AllowAny]  # Allow any user (authenticated or not) to access this view
    def post(self, request, *args, **kwargs):
        # Handle the webhook payload
        payload = None

        try:
            payload = request.data
            print("Received payload from request.data")
        except AttributeError:
            try:
                payload = request.json
                print("Received payload from request.json")
            except AttributeError:
                payload = request.body
                print("Received payload from request.body")

        print("Received Paystack webhook:", payload)

    
        if payload.get("event") == "subscription.create":
            customer_email = payload["data"]["customer"]["email"]
            print("Customer email:", customer_email)
            with schema_context('public'):
                # Find the tenant by email and update their subscription status
                tenant = Client.objects.get(email=customer_email)
                print("Tenant found:", tenant)
                tenant.paid_until = timezone.now() + timezone.timedelta(days=30)
                tenant.on_trial = False
                tenant.save()
                # Find the domain associated with the tenant
                domain = Domain.objects.get(tenant=tenant)
                print("Domain found:", domain)
                print("Tenant updated:", tenant)
                # Send confirmation email
                email_data = {
                    "to": [customer_email],
                    "subject": "Subscription Confirmed",
                    "body": f"Hello {tenant.name},\n\n Your subscription has been confirmed. Please log in to your account at https://{domain.domain}.\n\nThank you!",
                }
                send_mail(
                    email_data["subject"],
                    email_data["body"],
                    "lutherlunyamwi@gmail.com",
                    email_data["to"],
                    fail_silently=False,
                )
        else:
            print("Event is not subscription.create")
        return Response({"status": "success"}, status=200)