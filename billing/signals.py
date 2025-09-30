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
        "subject": "Subscription Link",
        "body": f"Hello {tenant.name},\n\n Your subscription link is: {subscription_link_mapper.get(tenant.subscription, 'No subscription plan selected')}\n\nThank you!",
    }
    send_mail(subject=email_data["subject"], message=email_data["body"], from_email="lutherlunyamwi@gmail.com", recipient_list=email_data["to"])