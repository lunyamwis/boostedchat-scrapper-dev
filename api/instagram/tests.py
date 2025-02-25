import os
from django.test import TestCase
from api.instagram.models import InstagramUser
from django_tenants.utils import schema_context


class InstagramUserTest(TestCase):
    @classmethod
    @schema_context(os.getenv('SCHEMA_NAME'))
    def setUpTestData(cls):
        InstagramUser.objects.create(username='test_user')

    @schema_context(os.getenv('SCHEMA_NAME'))
    def test_instagram_user_creation(self):
        user = InstagramUser.objects.get(username='test_user')
        print(f"{user.username} -------my tests are working")
        self.assertEqual(user.username, 'test_user')

    @schema_context(os.getenv('SCHEMA_NAME'))
    def test_instagram_user_str_representation(self):
        user = InstagramUser.objects.get(username='test_user')
        self.assertEqual(str(user), 'test_user')
