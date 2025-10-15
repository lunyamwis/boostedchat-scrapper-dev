import os
import logging
import requests
from django.dispatch import receiver
from django.core.mail import send_mail
from django_tenants.signals import post_schema_sync
from api.helpers.models import Client, Domain
from api.workflow.models import WorkflowModel, AirflowCreds
from django_tenants.utils import schema_context


@receiver(post_schema_sync)
def handle_tenant_created(sender, tenant, **kwargs):
    # setup domain
    
    print("Tenant created signal received for tenant:", tenant)
    # get plan code from tenant
    # import pdb;pdb.set_trace()
    instance = None
    if Client.objects.filter(schema_name=tenant).exists():
        instance = Client.objects.get(schema_name=tenant)
    else:
        import time
        interval = 5  # seconds
        elapsed = 0
        while True:
            if Client.objects.filter(schema_name=tenant).exists():
                instance = Client.objects.get(schema_name=tenant)
                logging.info(f"✅ Client with schema_name={tenant} found after {elapsed}s.")
                break
            time.sleep(interval)
            elapsed += interval
            logging.warning(f"⏱️ Still waiting for Client ({elapsed}s elapsed)... will retry in {interval}s.")

    domain = None
    if Domain.objects.filter(tenant=instance).exists():
        domain = Domain.objects.get(tenant=instance)
    else:
        try:

            domain = Domain(domain=instance.schema_name + '.lunyamwi.org', tenant=instance)
            domain.save()
        except Exception as e:
            logging.warning("Error creating domain:", e)

    airflow_base_url = "https://airflow.lunyamwi.org"
    with schema_context(instance.schema_name):
        acreds = AirflowCreds()
        acreds.airflow_base_url = airflow_base_url
        acreds.schema_name = instance.schema_name
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
        '0': f"https://{domain.domain}",
        '7000': 'https://paystack.shop/pay/0yiroqug8w',
        '10000': 'https://paystack.shop/pay/m43w86jxvo',
        '15000': 'https://paystack.shop/pay/gkdvhh0-1n',
    }

    from django.core.mail import EmailMultiAlternatives

    subject = "🎉 Welcome to Lunyamwi – Complete Your Subscription"
    from_email = "lutherlunyamwi@gmail.com"
    to = [instance.user.email]

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <h2 style="color: #2c3e50;">Hello {instance.name},</h2>

        <p>Welcome to <strong>Lunyamwi</strong>! 🎉<br>
        We’re thrilled to help you <strong>automate your social media</strong> and grow your brand 🚀.</p>

        <h3 style="color: #2c3e50;">📌 Subscription Details:</h3>
        <table style="border: 1px solid #ddd; padding: 10px; margin: 10px 0;">
        <tr><td><strong>Selected Plan</strong></td><td>{instance.subscription} KES / month</td></tr>
        <tr><td><strong>Next Step</strong></td>
            <td><a href="{subscription_link_mapper.get(instance.subscription, 'No subscription plan selected')}" 
                    style="color: #1a73e8; text-decoration: none;">Next Step</a></td>
        </tr>
        </table>

        <h3 style="color: #2c3e50;">✅ What’s included:</h3>
        <ul>
        <li>Automated responding on Whatsapp</li>
        <li>Social media listening & analytics</li>
        <li>Content scheduling & posting</li>
        <li>Performance tracking & reporting</li>
        </ul>

        <h3 style="color: #2c3e50;">💡 Upgrade or Switch Plans:</h3>
        <p>You can always choose a different plan anytime using the links below:</p>
        <ul>
        <li><a href="{subscription_link_mapper['7000']}">Starter (7,000 KES)</a></li>
        <li><a href="{subscription_link_mapper['10000']}">Basic (10,000 KES)</a></li>
        <li><a href="{subscription_link_mapper['15000']}">Professional (15,000 KES)</a></li>
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




    