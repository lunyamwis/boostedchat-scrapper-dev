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
                    "to": [tenant.user.email],
                    "subject": "🎉 Your Subscription is Confirmed – Welcome to Lunyamwi!"
                }
                email_body = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                    <meta charset="UTF-8" />
                    <style>
                        body {{
                        font-family: Arial, sans-serif;
                        background-color: #f9f9f9;
                        color: #333333;
                        padding: 20px;
                        }}
                        .container {{
                        max-width: 600px;
                        margin: auto;
                        background: #ffffff;
                        border-radius: 8px;
                        padding: 25px;
                        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                        }}
                        h2 {{
                        color: #2c3e50;
                        }}
                        p {{
                        line-height: 1.6;
                        }}
                        .btn {{
                        display: inline-block;
                        margin-top: 20px;
                        padding: 12px 20px;
                        background-color: #007bff;
                        color: #ffffff !important;
                        text-decoration: none;
                        border-radius: 5px;
                        font-weight: bold;
                        }}
                        .footer {{
                        margin-top: 25px;
                        font-size: 12px;
                        color: #888888;
                        text-align: center;
                        }}
                    </style>
                    </head>
                    <body>
                    <div class="container">
                        <h2>🎉 Subscription Confirmed</h2>
                        <p>Hello {tenant.name},</p>
                        <p>
                        Great news! Your subscription has been successfully confirmed.
                        </p>
                        <p>
                        You can now log in to your account using the same email and password you registered with.
                        </p>

                        <p style="text-align: center;">
                        <a href="https://{domain.domain}" class="btn">Log in to Your Account</a>
                        </p>

                        <h3>🔑 Login Details</h3>
                        <ul>
                        <li>Use the <strong>same email and password</strong> you registered with.</li>
                        </ul>

                        <h3>💡 Next Steps</h3>
                        <ul>
                        <li>Once logged in, you’ll be able to access your dashboard, set up automation workflows, and explore all your plan features.</li>
                        <li>If this is your first time, please allow up to 10 minutes for the system to fully set up your account.</li>
                        </ul>

                        <h3>📞 Need Help?</h3>
                        <p>
                        Our support team is ready to assist you. Simply reply to this email or visit our Help Center.
                        </p>

                        <p>
                        We’re excited to have you on board and can’t wait to see your brand grow 🚀.
                        </p>

                        <p>Warm regards,<br>
                        The <strong>[Your Tool Name]</strong> Team</p>

                        <div class="footer">
                        &copy; {2025} [Your Tool Name]. All rights reserved.
                        </div>
                    </div>
                    </body>
                    </html>
                    """


                send_mail(
                    subject=email_data["subject"],
                    message="This is the plain-text fallback for email clients that don’t support HTML.",
                    from_email="lutherlunyamwi@gmail.com",
                    recipient_list=email_data["to"],
                    html_message=email_body,
                    fail_silently=False,
                )


                
        else:
            print("Event is not subscription.create")
        return Response({"status": "success"}, status=200)