import json

from django.urls import include, path, reverse
from rest_framework import status
from rest_framework.test import APITestCase, URLPatternsTestCase

from .models import User


# Create your tests here.
class UserTest(APITestCase, URLPatternsTestCase):
    """Test module for User"""

    urlpatterns = [
        path("api/auth/", include("api.authentication.urls")),
    ]

    def setUp(self):
        self.user1 = User.objects.create_user(
            email="test1@test.com",
            password="test",
        )

        self.admin = User.objects.create_superuser(
            email="admin@test.com",
            password="admin",
        )

    def test_login(self):
        """Test if a user can login and get a JWT response token"""
        url = reverse("login")
        data = {"email": "admin@test.com", "password": "admin"}
        response = self.client.post(url, data)
        response_data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["success"], True)
        self.assertTrue("access" in response_data)

    def test_user_registration(self):
        """Test if a user can register"""
        url = reverse("register")
        data = {
            "email": "test2@test.com",
            "password": "test",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
