from django.test import TestCase

# Create your tests here.
from django.test import TestCase
import requests
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LinkedinTests(TestCase):
    url = os.getenv("API_URL", "")

    def test_linkedin_accounts(self):
        response = requests.get(f"{self.url}/linkedin/accounts/")
        if response.status_code != 200:
            self.fail(f"Error fetching LinkedIn accounts: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn Accounts Response: {response.json()}")

    def test_connect_linkedin_account(self):
        connect_or_not = input("Do you want to connect a new LinkedIn account? (yes/no): ").strip().lower()
        if connect_or_not != 'yes':
            self.skipTest("Skipping LinkedIn account connection test.")
        
        email = input("Enter LinkedIn username (email): ").strip()
        password = input("Enter LinkedIn password: ").strip()   
        payload = {
            "username": email,
            "password": password,
            "country": "ke",
            "city": "nairobi"
        }
        response = requests.post(f"{self.url}/linkedin/accounts/", json=payload)

        print(response.json())
        print("Store the account ID for future tests in an environment variable known as LINKEDIN_TEST_ACCOUNT_ID.")
        if "checkpoint" in response.json().get("data", {}).keys():
            print("Checkpoint required. Please solve the checkpoint.")
            account_id = response.json().get("data", {}).get("account_id")
            code = input("Enter the challenge code sent to your email or phone: ")
            payload = {
                "account_id": account_id,
                "code": str(code)
            }
            print(f"Solving checkpoint for account ID: {account_id}")
            response = requests.post(f"{self.url}/linkedin/accounts/checkpoint/", json=payload)
            if response.status_code != 201:
                self.fail(f"Error creating LinkedIn account: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 201)
        print(f"LinkedIn Account Created: {response.json()}")

    def test_reconnect_linkedin_account(self):
        reconnect_or_not = input("Do you want to reconnect a LinkedIn account? (yes/no): ").strip().lower()
        if reconnect_or_not != 'yes':
            self.skipTest("Skipping LinkedIn account reconnection test.")
        
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            self.fail("LINKEDIN_TEST_ACCOUNT_ID environment variable not set.")

        email = input("Enter LinkedIn username (email): ").strip()
        password = input("Enter LinkedIn password: ").strip()
        payload = {
            "username": email,
            "password": password,
            "country": "ke",
            "city": "nairobi"
        }
        response = requests.post(f"{self.url}/linkedin/accounts/{account_id}/", json=payload)
        if "checkpoint" in response.json().get("data", {}).keys():
            print("Checkpoint required. Please solve the checkpoint.")
            account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
            code = input("Enter the challenge code sent to your email or phone: ")
            payload = {
                "account_id": account_id,
                "code": str(code)
            }
            print(f"Solving checkpoint for account ID: {account_id}")
            response = requests.post(f"{self.url}/linkedin/accounts/checkpoint/", json=payload)    
            if response.status_code != 200 and response.status_code != 201:
                self.fail(f"Error reconnecting LinkedIn account: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        print(f"LinkedIn Account Reconnected: {response.json()}")

    def test_linkedin_account_detail(self):
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/")
        if response.status_code != 200:
            self.fail(f"Error fetching LinkedIn account details: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
    

    def test_linkedin_account_delete(self):
        delete_or_not = input("Do you want to delete a LinkedIn account? (yes/no): ").strip().lower()
        if delete_or_not != 'yes':
            self.skipTest("Skipping LinkedIn account deletion test.")
        
        account_id = input("Enter the LinkedIn account ID to delete: ").strip()
        response = requests.delete(f"{self.url}/linkedin/accounts/{account_id}/")
        if response.status_code != 200 and response.status_code != 204:
            self.fail(f"Error deleting LinkedIn account: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 204])
        print("LinkedIn Account Deleted Successfully")

    def test_linkedin_chats(self):
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/chats/")
        if response.status_code != 200:
            self.fail(f"Error fetching LinkedIn chats: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn Chats Response: {response.json()}")

    def test_linkedin_chat_post(self):
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        attendees_input = input("Enter comma-separated LinkedIn user IDs to chat with (or leave blank to skip): ").strip()
        if not attendees_input:
            self.skipTest("Skipping LinkedIn chat creation test.")
        attendees_ids = [attendee.strip() for attendee in attendees_input.split(",") if attendee.strip()]
        message = input("Enter the message to send: ").strip()
        if not message:
            self.skipTest("No message provided. Skipping LinkedIn chat creation test.")
        payload = {
            "attendees_ids": attendees_ids,
            "text": message
        }
        response = requests.post(f"{self.url}/linkedin/accounts/{account_id}/chats/", json=payload)
        if response.status_code != 201 and response.status_code != 200:
            self.fail(f"Error sending LinkedIn chat message: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [201, 200])

    def test_linkedin_chat_detail(self):
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        chat_id = input("Enter the LinkedIn chat ID to fetch details: ").strip()
        if not chat_id:
            self.skipTest("No chat ID provided. Skipping LinkedIn chat detail test.")
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/chats/{chat_id}/")
        if response.status_code != 200:
            self.fail(f"Error fetching LinkedIn chat details: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn Chat Detail Response: {response.json()}")
    
    def test_linkedin_chat_messages(self):
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        chat_id = input("Enter the LinkedIn chat ID to fetch messages: ").strip()
        if not chat_id:
            self.skipTest("No chat ID provided. Skipping LinkedIn chat messages test.")
        
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/chats/{chat_id}/messages/")
        if response.status_code != 200:
            self.fail(f"Error fetching LinkedIn chat messages: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_linkedin_chat_message_post(self):
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        chat_id = input("Enter the LinkedIn chat ID to send a message: ").strip()
        if not chat_id:
            self.skipTest("No chat ID provided. Skipping LinkedIn chat message post test.")
        message = input("Enter the message to send: ").strip()
        if not message:
            self.skipTest("No message provided. Skipping LinkedIn chat message post test.")
        payload = {
            "account_id": account_id,
            "text": message
        }
        response = requests.post(f"{self.url}/linkedin/accounts/{account_id}/chats/{chat_id}/messages/", json=payload)
        if response.status_code != 201 and response.status_code != 200:
            self.fail(f"Error sending LinkedIn chat message: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [201, 200])

    def test_linkedin_chat_attendees(self):
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        chat_id = input("Enter the LinkedIn chat ID to fetch attendees: ").strip()
        if not chat_id:
            self.skipTest("No chat ID provided. Skipping LinkedIn chat attendees test.")
        
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/chats/{chat_id}/attendees/")
        if response.status_code != 200:
            self.fail(f"Error fetching LinkedIn chat attendees: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn Chat Attendees Response: {response.json()}")


    def test_linkedin_chat_sync(self):
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        chat_id = input("Enter the LinkedIn chat ID to sync messages: ").strip()
        if not chat_id:
            self.skipTest("No chat ID provided. Skipping LinkedIn chat sync test.")
        
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/chats/{chat_id}/sync/")
        if response.status_code != 200 and response.status_code != 201:
            self.fail(f"Error syncing LinkedIn chat messages: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"LinkedIn Chat Sync Response: {response.json()}")

    def test_linkedin_message_detail(self):
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        message_id = input("Enter the LinkedIn message ID to fetch details: ").strip()
        if not message_id:
            self.skipTest("No message ID provided. Skipping LinkedIn message detail test.")
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/messages/{message_id}/")
        if response.status_code != 200:
            self.fail(f"Error fetching LinkedIn message details: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn Message Detail Response: {response.json()}")

    def test_retrieve_linkedin_message_attachment(self):
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        message_id = os.getenv("MESSAGE_ID", "")
        attachment_id = input("Enter the LinkedIn message attachment ID to retrieve: ").strip()
        if not message_id or not attachment_id:
            self.skipTest("No message ID or attachment ID provided. Skipping LinkedIn message attachment retrieval test.")
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/messages/{message_id}/attachments/{attachment_id}/")
        if response.status_code != 200:
            self.fail(f"Error retrieving LinkedIn message attachment: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn Message Attachment Response: {response.json()}")

    def test_linkedin_chat_attendees(self):
        response = requests.get(f"{self.url}/linkedin/accounts/chats/all_attendees")
        if response.status_code != 200 and response.status_code != 201:
            self.fail(f"Error adding attendees to LinkedIn chat: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"LinkedIn Chat Add Attendees Response: {response.json()}")

    def test_linkedin_chat_attendee_detail(self):
        attendee_id = input("Enter the LinkedIn chat attendee ID to fetch details: ").strip()
        if not attendee_id:
            self.skipTest("No attendee ID provided. Skipping LinkedIn chat attendee detail test.")
        response = requests.get(f"{self.url}/linkedin/accounts/chats/all_attendees/{attendee_id}")
        if response.status_code != 200:
            self.fail(f"Error fetching LinkedIn chat attendee details: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn Chat Attendee Detail Response: {response.json()}")

    def test_chat_attendee_chats(self):
        attendee_id = input("Enter the LinkedIn chat attendee ID to fetch their chats: ").strip()
        if not attendee_id:
            self.skipTest("No attendee ID provided. Skipping LinkedIn chat attendee chats test.")
        response = requests.get(f"{self.url}/linkedin/accounts/chats/all_attendees/{attendee_id}/chats/")
        if response.status_code != 200:
            self.fail(f"Error fetching LinkedIn chat attendee's chats: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn Chat Attendee Chats Response: {response.json()}")
    
    def test_chat_attendee_messages(self):
        sender_id = input("Enter the LinkedIn chat attendee ID to fetch their messages: ").strip()
        if not sender_id:
            self.skipTest("No attendee ID provided. Skipping LinkedIn chat attendee messages test.")
        response = requests.get(f"{self.url}/linkedin/accounts/chats/all_attendees/{sender_id}/messages/")
        if response.status_code != 200:
            self.fail(f"Error fetching LinkedIn chat attendee's messages: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn Chat Attendee Messages Response: {response.json()}")
