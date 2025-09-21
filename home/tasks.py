from celery import shared_task
from api.helpers.models import Client, Domain
from django.utils import timezone
from django_tenants.utils import schema_context
from api.authentication.models import User

@shared_task
def create_tenant(domain_name=None, email=None, subscription=None, phone_number=None):
    with schema_context('public'):
        user = User.objects.get(email=email)
        tenant = Client(schema_name=domain_name, name=domain_name, paid_until=timezone.now() + timezone.timedelta(days=7), on_trial=True)
        tenant.user = user
        tenant.email = email
        tenant.subscription = subscription
        tenant.phone_number_id = phone_number
        tenant.save()
        domain = Domain(domain=domain_name + '.lunyamwi.org', tenant=tenant)
        domain.save()
