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

    # send credentials email
    email_data = {
        "to": [tenant.user.email],
        "subject": "Welcome to Lunyamwi 🎉 – Complete Your Subscription",
        "body": f"""
        Hello {tenant.name},

        Welcome to Lunyamwi! 🎉 We're excited to help you automate your social media and grow your brand.

        Here are your subscription details:
        -------------------------------------------------
        Selected Plan: {tenant.subscription} KES / month
        Subscription Link: {subscription_link_mapper.get(tenant.subscription, 'No subscription plan selected')}
        -------------------------------------------------

        ✅ What you get with this plan:
        - Automated responding on supported platforms
        - Social media listening & analytics
        - Content scheduling & posting
        - Performance tracking

        💡 Need to upgrade or switch plans?
        You can always choose a different plan using the links below:
        - Micro (2,000 KES): {subscription_link_mapper['2000']}
        - Starter (5,000 KES): {subscription_link_mapper['5000']}
        - Basic (10,000 KES): {subscription_link_mapper['10000']}
        - Professional (20,000 KES): {subscription_link_mapper['20000']}
        - Enterprise (50,000 KES): {subscription_link_mapper['50000']}

        📞 Need help?
        Our support team is here for you. Simply reply to this email or visit our Help Center.

        We’re thrilled to have you on board and can’t wait to see your success 🚀.

        Warm regards,  
        The Lunyamwi Team
        """,
    }

    send_mail(
        subject=email_data["subject"], 
        message=email_data["body"], 
        from_email="lutherlunyamwi@gmail.com", 
        recipient_list=email_data["to"]
    )



    