from django.test import TestCase

# Create your tests here.
from django.test import TestCase
import requests
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GmailTests(TestCase):
    url = os.getenv("API_URL", "")

    def test_gmail_connect_accounts_connection(self):
        connect_or_not = input("Do you want to connect a Gmail account? (y/n): ")
        if connect_or_not.lower() == 'y':
            payload = {
                "provider": "GOOGLE_OAUTH",
                "refresh_token": os.getenv("GMAIL_REFRESH_TOKEN", ""),
                "access_token": os.getenv("GMAIL_ACCESS_TOKEN", "")
            }
            response = requests.post(f"{self.url}/gmail/accounts/", json=payload)
            logger.info(f"Response Status Code: {response.status_code}")
            if response.status_code != 200 and response.status_code != 201:
                self.fail(f"Failed to connect Gmail account: {response.text}")
            self.assertIn(response.status_code, [200, 201])
            logger.info(f"Response Data: {response.json()}")
        else:
            self.skipTest("Skipping Gmail account connection test.")
