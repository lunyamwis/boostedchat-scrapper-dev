import pytest
from pytest_factoryboy import register

from tests.factories import InstagramUserFactory

register(InstagramUserFactory)

# @pytest.fixture
# def instagram_user():
#     return InstagramUserFactory()

@pytest.fixture(scope="session")
def default_tenant(django_db_setup, django_db_blocker):
    """
    Create a test tenant with the default schema.
    """
    with django_db_blocker.unblock():
        tenant = Client.objects.create(
            schema_name="test_schema",  # Change as needed
            name="Test Tenant",
            paid_until="2099-12-31",
            on_trial=False,
        )
        tenant.save()
    return tenant

@pytest.fixture
def tenant_schema(default_tenant):
    """
    Switch to the test tenant's schema.
    """
    with schema_context(default_tenant.schema_name):
        yield default_tenant