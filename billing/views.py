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
                    "subject": "🎉 Subscription Confirmed – Welcome to Lunyamwi",
                    "body": f"""
                        Hello {tenant.name},

                        Great news! Your subscription has been successfully confirmed. 🎉  

                        You can now log in to your account here:
                        👉 https://{domain.domain}

                        🔑 Login details:
                        - Use the **same email and password** you registered with when getting started.

                        💡 Next Steps:
                        - Once logged in, you’ll be able to access your dashboard, set up automation workflows, and explore all your plan features.
                        - If this is your first time, please allow up to 10 minutes for the system to fully set up your account.

                        📞 Need help?
                        Our support team is ready to assist you. Simply reply to this email or visit our Help Center.

                        We’re excited to have you on board and can’t wait to see your brand grow 🚀.

                        Warm regards,  
                        The Lunyamwi Team
                    """,
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