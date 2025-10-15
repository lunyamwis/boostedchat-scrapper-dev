import os
import time
import requests
from django.dispatch import receiver
from django.core.mail import send_mail
from django_tenants.signals import post_schema_sync
from api.helpers.models import Client, Domain
from api.workflow.models import WorkflowModel, AirflowCreds
from django_tenants.utils import schema_context

import time
import logging
from django.db import models

logger = logging.getLogger(__name__)

@schema_context('public')
def wait_for_model(model: models.Model, filter_kwargs: dict, interval: int = 10):
    """
    Wait indefinitely for a Django model instance to appear in the database.

    Args:
        model: Django model class (e.g. Client, Domain)
        filter_kwargs: Query filter to match the object (e.g. {"schema_name": "tenant1"})
        interval: Seconds between checks (default: 10)

    Returns:
        The model instance once found.
    """
    model_name = model.__name__
    logger.info(f"⏳ Waiting for {model_name} with {filter_kwargs} (checking every {interval}s)...")

    elapsed = 0
    while True:
        if model.objects.filter(**filter_kwargs).exists():
            instance = model.objects.get(**filter_kwargs)
            logger.info(f"✅ {model_name} with {filter_kwargs} found after {elapsed}s.")
            return instance

        time.sleep(interval)
        elapsed += interval
        logger.warning(f"⏱️ Still waiting for {model_name} ({elapsed}s elapsed)... will retry in {interval}s.")


@receiver(post_schema_sync)
def handle_tenant_created(sender, tenant, **kwargs):
    # setup domain
    
    print("Tenant created signal received for tenant:", tenant)
    # get plan code from tenant
    # import pdb;pdb.set_trace()
    tenant = wait_for_model(Client, {"schema_name": tenant})
    domain = wait_for_model(Domain, {"tenant__schema_name": tenant})
    airflow_base_url = "https://airflow.lunyamwi.org"
    with schema_context(tenant.schema_name):
        acreds = AirflowCreds()
        acreds.airflow_base_url = airflow_base_url
        acreds.schema_name = tenant.schema_name
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
        <tr><td><strong>Next Step</strong></td>
            <td><a href="{subscription_link_mapper.get(tenant.subscription, 'No subscription plan selected')}" 
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




    