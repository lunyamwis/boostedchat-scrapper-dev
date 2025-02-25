import factory
from faker import Faker
from api.instagram.models import ( 
    InstagramUser,
    AirflowCreds, 
    HttpOperatorConnectionModel,
    DagModel,
    CustomField,
    CustomFieldValue,
    Endpoint,
    PostgresOperatorModel,
    SimpleHttpOperatorModel,
    Media
    )

fake = Faker()

class InstagramUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InstagramUser

    username = 'test_user'
    