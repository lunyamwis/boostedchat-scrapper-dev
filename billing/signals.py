import os
import requests
from django.dispatch import receiver
from django.core.mail import send_mail
from django_tenants.signals import post_schema_sync
from api.helpers.models import Client
from api.workflow.models import WorkflowModel, AirflowCreds


@receiver(post_schema_sync)
def handle_tenant_created(sender, tenant, **kwargs):
    # setup domain
    
    print("Tenant created signal received for tenant:", tenant)
    # get plan code from tenant
    # import pdb;pdb.set_trace()
    tenant = Client.objects.get(schema_name=tenant)

    airflow_base_url = "https://airflow.lunyamwi.org"
    acreds = AirflowCreds()
    acreds.airflow_base_url = airflow_base_url
    acreds.username = os.getenv("AIRFLOW_USERNAME","airflow")
    acreds.password = os.getenv("AIRFLOW_PASSWORD","airflow")
    acreds.save()
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    token = None        
    resp = requests.post(
        f"{airflow_base_url}/auth/token",
        json={"username": acreds.username, "password": acreds.password},
        headers=headers
    )
    
    if resp.status_code in [200, 201]:
        token = resp.json()["access_token"]
        acreds.airflow_token = token
        acreds.save()
    else:
        print("Failed to get Airflow token:", resp.text)
    
    subscription_link_mapper = {
        '2000': 'https://paystack.shop/pay/0yiroqug8w',
        '5000': 'https://paystack.shop/pay/m43w86jxvo',
        '10000': 'https://paystack.shop/pay/gkdvhh0-1n',
        '20000': 'https://paystack.shop/pay/unw4mh897x',
        '50000': 'https://paystack.shop/pay/r-uteymt-4',
    }

    from django.core.mail import EmailMultiAlternatives

    subject = "🎉 Welcome to Lunyamwi – Complete Your Subscription"
    from_email = "lutherlunyamwi@gmail.com"
    to = [tenant.user.email]

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <h2 style="color: #2c3e50;">Hello {tenant.name},</h2>

        <p>Welcome to <strong>Lunyamwi</strong>! 🎉<br>
        We’re thrilled to help you <strong>automate your social media</strong> and grow your brand 🚀.</p>

        <h3 style="color: #2c3e50;">📌 Subscription Details:</h3>
        <table style="border: 1px solid #ddd; padding: 10px; margin: 10px 0;">
        <tr><td><strong>Selected Plan</strong></td><td>{tenant.subscription} KES / month</td></tr>
        <tr><td><strong>Subscription Link</strong></td>
            <td><a href="{subscription_link_mapper.get(tenant.subscription, 'No subscription plan selected')}" 
                    style="color: #1a73e8; text-decoration: none;">Complete Payment Here</a></td>
        </tr>
        </table>

        <h3 style="color: #2c3e50;">✅ What’s included:</h3>
        <ul>
        <li>Automated responding on LinkedIn, Facebook, WhatsApp, Instagram & Email</li>
        <li>Social media listening & analytics</li>
        <li>Content scheduling & posting</li>
        <li>Performance tracking & reporting</li>
        </ul>

        <h3 style="color: #2c3e50;">💡 Upgrade or Switch Plans:</h3>
        <p>You can always choose a different plan anytime using the links below:</p>
        <ul>
        <li><a href="{subscription_link_mapper['2000']}">Micro (2,000 KES)</a></li>
        <li><a href="{subscription_link_mapper['5000']}">Starter (5,000 KES)</a></li>
        <li><a href="{subscription_link_mapper['10000']}">Basic (10,000 KES)</a></li>
        <li><a href="{subscription_link_mapper['20000']}">Professional (20,000 KES)</a></li>
        <li><a href="{subscription_link_mapper['50000']}">Enterprise (50,000 KES)</a></li>
        </ul>

        <h3 style="color: #2c3e50;">📞 Need Help?</h3>
        <p>Our support team is always here for you. Simply reply to this email or visit our Help Center.</p>

        <p>We’re excited to have you on board and can’t wait to see your success with <strong>Lunyamwi</strong> 🚀.</p>

        <p style="margin-top:20px;">Warm regards,<br>
        <strong>The Lunyamwi Team</strong></p>
    </body>
    </html>
    """

    msg = EmailMultiAlternatives(subject, "", from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()




    