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


    def test_linkedin_user_invitations_sent(self):
        """Test fetching sent LinkedIn invitations"""
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            account_id = input("Enter LinkedIn account ID to fetch sent invitations: ").strip()
        if not account_id:
            self.skipTest("No account ID provided. Skipping LinkedIn sent invitations test.")
        
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/users/invitations/sent/")
        if response.status_code != 200:
            self.fail(f"Error fetching LinkedIn sent invitations: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn Sent Invitations Response: {response.json()}")

    def test_linkedin_user_invitations_received(self):
        """Test fetching received LinkedIn invitations"""
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            account_id = input("Enter LinkedIn account ID to fetch received invitations: ").strip()
        if not account_id:
            self.skipTest("No account ID provided. Skipping LinkedIn received invitations test.")
        
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/users/invitations/received/")
        if response.status_code != 200:
            self.fail(f"Error fetching LinkedIn received invitations: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn Received Invitations Response: {response.json()}")

    def test_linkedin_handle_invitation(self):
        """Test handling LinkedIn invitation (accept/decline)"""
        invitation_id = input("Enter LinkedIn invitation ID to handle (or leave blank to skip): ").strip()
        if not invitation_id:
            self.skipTest("No invitation ID provided. Skipping LinkedIn invitation handling test.")
        
        action = input("Enter action (ACCEPT/DECLINE): ").strip().upper()
        if action not in ['ACCEPT', 'DECLINE']:
            self.skipTest("Invalid action provided. Skipping LinkedIn invitation handling test.")
        
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            account_id = input("Enter LinkedIn account ID: ").strip()
        
        payload = {
            "provider": "LINKEDIN",
            "action": action,
            "shared_secret": "",
            "account_id": account_id
        }
        
        response = requests.post(f"{self.url}/linkedin/users/invitations/{invitation_id}/handle/", json=payload)
        if response.status_code not in [200, 201]:
            self.fail(f"Error handling LinkedIn invitation: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"LinkedIn Invitation Handled Response: {response.json()}")

    def test_linkedin_delete_invitation(self):
        """Test deleting LinkedIn invitation"""
        invitation_id = input("Enter LinkedIn invitation ID to delete (or leave blank to skip): ").strip()
        if not invitation_id:
            self.skipTest("No invitation ID provided. Skipping LinkedIn invitation deletion test.")
        
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            account_id = input("Enter LinkedIn account ID: ").strip()
        
        response = requests.delete(f"{self.url}/linkedin/users/invitations/{invitation_id}/handle/?account_id={account_id}")
        if response.status_code not in [200, 204]:
            self.fail(f"Error deleting LinkedIn invitation: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 204])
        logger.info(f"LinkedIn Invitation Deleted Response: {response.json()}")

    def test_linkedin_send_invitation(self):
        """Test sending LinkedIn connection invitation"""
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            account_id = input("Enter LinkedIn account ID: ").strip()
        if not account_id:
            self.skipTest("No account ID provided. Skipping LinkedIn send invitation test.")
        
        provider_id = input("Enter LinkedIn user ID to send invitation to (or leave blank to skip): ").strip()
        if not provider_id:
            self.skipTest("No provider ID provided. Skipping LinkedIn send invitation test.")
        
        # user_email = input("Enter user email (optional): ").strip()
        message = input("Enter invitation message (optional): ").strip()
        
        payload = {
            "provider_id": provider_id,
            "account_id": account_id,
            # "user_email": "",
            "message": message
        }
        
        response = requests.post(f"{self.url}/linkedin/accounts/{account_id}/users/invitations/send/", json=payload)
        if response.status_code not in [200, 201]:
            self.fail(f"Error sending LinkedIn invitation: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"LinkedIn Invitation Sent Response: {response.json()}")

    def test_linkedin_user_profile(self):
        """Test fetching LinkedIn user profile"""
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            account_id = input("Enter LinkedIn account ID: ").strip()
        if not account_id:
            self.skipTest("No account ID provided. Skipping LinkedIn user profile test.")
        
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/users/profile/")
        if response.status_code != 200:
            self.fail(f"Error fetching LinkedIn user profile: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn User Profile Response: {response.json()}")

    def test_linkedin_edit_profile(self):
        """Test editing LinkedIn user profile"""
        edit_profile = input("Do you want to edit LinkedIn profile? (yes/no): ").strip().lower()
        if edit_profile != 'yes':
            self.skipTest("Skipping LinkedIn profile edit test.")
        
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            account_id = input("Enter LinkedIn account ID: ").strip()
        if not account_id:
            self.skipTest("No account ID provided. Skipping LinkedIn profile edit test.")
        
        first_name = input("Enter first name (optional): ").strip()
        last_name = input("Enter last name (optional): ").strip()
        headline = input("Enter headline (optional): ").strip()
        
        payload = {
            "account_id": account_id,
            "first_name": first_name,
            "last_name": last_name,
            "headline": headline
        }
        
        response = requests.patch(f"{self.url}/linkedin/accounts/{account_id}/users/profile/edit/", json=payload)
        if response.status_code not in [200, 201]:
            self.fail(f"Error editing LinkedIn profile: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"LinkedIn Profile Edit Response: {response.json()}")

    def test_linkedin_user_relations(self):
        """Test fetching LinkedIn user relations"""
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            account_id = input("Enter LinkedIn account ID: ").strip()
        if not account_id:
            self.skipTest("No account ID provided. Skipping LinkedIn user relations test.")
        
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/users/relations/")
        if response.status_code != 200:
            self.fail(f"Error fetching LinkedIn user relations: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn User Relations Response: {response.json()}")

    
    def test_linkedin_user_followers(self):
        """Test fetching LinkedIn user followers"""
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            account_id = input("Enter LinkedIn account ID: ").strip()
        if not account_id:
            self.skipTest("No account ID provided. Skipping LinkedIn user followers test.")
        
        user_id = input("Enter user ID to fetch followers for (optional): ").strip()
        
        params = {}
        if user_id:
            params['user_id'] = user_id
        
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/users/followers/", params=params)
        if response.status_code != 200:
            self.fail(f"Error fetching LinkedIn user followers: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn User Followers Response: {response.json()}")

    def test_linkedin_retrieve_user_profile(self):
        """Test retrieving specific LinkedIn user profile"""
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            account_id = input("Enter LinkedIn account ID: ").strip()
        if not account_id:
            self.skipTest("No account ID provided. Skipping LinkedIn retrieve user profile test.")
        
        identifier = input("Enter LinkedIn user ID or vanity name to retrieve: ").strip()
        if not identifier:
            self.skipTest("No identifier provided. Skipping LinkedIn retrieve user profile test.")
        
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/users/{identifier}/profile/")
        if response.status_code != 200:
            self.fail(f"Error retrieving LinkedIn user profile: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn User Profile Retrieved Response: {response.json()}")

    def test_linkedin_user_posts(self):
        """Test fetching LinkedIn user posts"""
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            account_id = input("Enter LinkedIn account ID: ").strip()
        if not account_id:
            self.skipTest("No account ID provided. Skipping LinkedIn user posts test.")
        
        identifier = input("Enter LinkedIn user ID or vanity name to fetch posts: ").strip()
        if not identifier:
            self.skipTest("No identifier provided. Skipping LinkedIn user posts test.")
        
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/users/{identifier}/posts/")
        if response.status_code != 200:
            self.fail(f"Error fetching LinkedIn user posts: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn User Posts Response: {response.json()}")

    def test_linkedin_user_comments(self):
        """Test fetching LinkedIn user comments"""
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            account_id = input("Enter LinkedIn account ID: ").strip()
        if not account_id:
            self.skipTest("No account ID provided. Skipping LinkedIn user comments test.")
        
        identifier = input("Enter LinkedIn user ID or vanity name to fetch comments: ").strip()
        if not identifier:
            self.skipTest("No identifier provided. Skipping LinkedIn user comments test.")
        
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/users/{identifier}/comments/")
        if response.status_code != 200:
            self.fail(f"Error fetching LinkedIn user comments: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn User Comments Response: {response.json()}")

    def test_linkedin_user_reactions(self):
        """Test fetching LinkedIn user reactions"""
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            account_id = input("Enter LinkedIn account ID: ").strip()
        if not account_id:
            self.skipTest("No account ID provided. Skipping LinkedIn user reactions test.")
        
        identifier = input("Enter LinkedIn user ID or vanity name to fetch reactions: ").strip()
        if not identifier:
            self.skipTest("No identifier provided. Skipping LinkedIn user reactions test.")
        
        reaction_type = input("Enter reaction type filter (LIKE, LOVE, CELEBRATE, etc.) or leave blank: ").strip()
        
        params = {}
        if reaction_type:
            params['reaction_type'] = reaction_type
        
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/users/{identifier}/reactions/", params=params)
        if response.status_code != 200:
            self.fail(f"Error fetching LinkedIn user reactions: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn User Reactions Response: {response.json()}")

    def test_linkedin_post_retrieve(self):
        """Test retrieving a LinkedIn post"""
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            self.skipTest("No account ID provided. Skipping LinkedIn post retrieve test.")
        
        post_id = input("Enter LinkedIn post ID to retrieve: ").strip()
        if not post_id:
            self.skipTest("No post ID provided. Skipping LinkedIn post retrieve test.")
        
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/posts/{post_id}/")
        if response.status_code != 200:
            self.fail(f"Error retrieving LinkedIn post: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn Post Retrieve Response: {response.json()}")

    def test_linkedin_create_post(self):
        """Test creating a LinkedIn post"""
        create_post = input("Do you want to create a LinkedIn post? (yes/no): ").strip().lower()
        if create_post != 'yes':
            self.skipTest("Skipping LinkedIn create post test.")
        
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            self.skipTest("No account ID provided. Skipping LinkedIn create post test.")
        
        text = input("Enter post text: ").strip()
        if not text:
            self.skipTest("No post text provided. Skipping LinkedIn create post test.")
        
        payload = {
            "text": text,
            "visibility": "PUBLIC"
        }
        
        response = requests.post(f"{self.url}/linkedin/accounts/{account_id}/posts/", json=payload)
        if response.status_code not in [200, 201]:
            self.fail(f"Error creating LinkedIn post: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"LinkedIn Create Post Response: {response.json()}")

    def test_linkedin_post_comments_get(self):
        """Test getting LinkedIn post comments"""
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            self.skipTest("No account ID provided. Skipping LinkedIn post comments test.")
        
        post_id = input("Enter LinkedIn post ID to get comments: ").strip()
        if not post_id:
            self.skipTest("No post ID provided. Skipping LinkedIn post comments test.")
        
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/posts/{post_id}/comments/")
        if response.status_code != 200:
            self.fail(f"Error getting LinkedIn post comments: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn Post Comments Response: {response.json()}")

    def test_linkedin_post_comments_create(self):
        """Test adding a comment to LinkedIn post"""
        add_comment = input("Do you want to add a comment to a LinkedIn post? (yes/no): ").strip().lower()
        if add_comment != 'yes':
            self.skipTest("Skipping LinkedIn add comment test.")
        
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            self.skipTest("No account ID provided. Skipping LinkedIn add comment test.")
        
        post_id = input("Enter LinkedIn post ID to comment on: ").strip()
        if not post_id:
            self.skipTest("No post ID provided. Skipping LinkedIn add comment test.")
        
        text = input("Enter comment text: ").strip()
        if not text:
            self.skipTest("No comment text provided. Skipping LinkedIn add comment test.")
        
        payload = {
            "text": text
        }
        
        response = requests.post(f"{self.url}/linkedin/accounts/{account_id}/posts/{post_id}/comments/", json=payload)
        if response.status_code not in [200, 201]:
            self.fail(f"Error adding LinkedIn comment: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"LinkedIn Add Comment Response: {response.json()}")

    def test_linkedin_post_reactions_get(self):
        """Test getting LinkedIn post reactions"""
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            self.skipTest("No account ID provided. Skipping LinkedIn post reactions test.")
        
        post_id = input("Enter LinkedIn post ID to get reactions: ").strip()
        if not post_id:
            self.skipTest("No post ID provided. Skipping LinkedIn post reactions test.")
        
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/posts/{post_id}/reactions/")
        if response.status_code != 200:
            self.fail(f"Error getting LinkedIn post reactions: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn Post Reactions Response: {response.json()}")

    def test_linkedin_post_reactions_create(self):
        """Test reacting to a LinkedIn post"""
        react_to_post = input("Do you want to react to a LinkedIn post? (yes/no): ").strip().lower()
        if react_to_post != 'yes':
            self.skipTest("Skipping LinkedIn react to post test.")
        
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            self.skipTest("No account ID provided. Skipping LinkedIn react to post test.")
        
        post_id = input("Enter LinkedIn post ID to react to: ").strip()
        if not post_id:
            self.skipTest("No post ID provided. Skipping LinkedIn react to post test.")
        
        reaction_type = input("Enter reaction type (like, love, celebrate, support, insightful, funny): ").strip().lower()
        if not reaction_type:
            reaction_type = "like"
        
        payload = {
            "reaction_type": reaction_type
        }
        
        response = requests.post(f"{self.url}/linkedin/accounts/{account_id}/posts/{post_id}/reactions/", json=payload)
        if response.status_code not in [200, 201]:
            self.fail(f"Error reacting to LinkedIn post: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"LinkedIn React to Post Response: {response.json()}")

    def test_linkedin_company_profile(self):
        """Test fetching LinkedIn company profile"""
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            self.skipTest("No account ID provided. Skipping LinkedIn company profile test.")
        
        identifier = input("Enter company identifier (ID or name): ").strip()
        if not identifier:
            self.skipTest("No company identifier provided. Skipping LinkedIn company profile test.")
        
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/company/{identifier}/")
        if response.status_code != 200:
            self.fail(f"Error fetching LinkedIn company profile: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn Company Profile Response: {response.json()}")

    def test_linkedin_inmail_balance(self):
        """Test fetching LinkedIn InMail balance"""
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            self.skipTest("No account ID provided. Skipping LinkedIn InMail balance test.")
        
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/inmail/balance/")
        if response.status_code != 200:
            self.fail(f"Error fetching LinkedIn InMail balance: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn InMail Balance Response: {response.json()}")

    def test_linkedin_search_parameters(self):
        """Test fetching LinkedIn search parameters"""
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            self.skipTest("No account ID provided. Skipping LinkedIn search parameters test.")
        
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/search/parameters/")
        if response.status_code != 200:
            self.fail(f"Error fetching LinkedIn search parameters: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn Search Parameters Response: {response.json()}")

    def test_linkedin_search(self):
        """Test LinkedIn search functionality"""
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            self.skipTest("No account ID provided. Skipping LinkedIn search test.")
        
        keywords = input("Enter search keywords: ").strip()
        if not keywords:
            keywords = "developer"
        
        params = {'keywords': keywords, 'category': 'people'}
        response = requests.post(f"{self.url}/linkedin/accounts/{account_id}/search/", json=params)
        if response.status_code != 200:
            self.fail(f"Error performing LinkedIn search: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn Search Response: {response.json()}")

    def test_linkedin_job_postings_get(self):
        """Test fetching LinkedIn job postings"""
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            self.skipTest("No account ID provided. Skipping LinkedIn job postings test.")
        
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/jobs/")
        if response.status_code != 200:
            self.fail(f"Error fetching LinkedIn job postings: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn Job Postings Response: {response.json()}")
    
    def test_linkedin_job_posting_create(self):
        """Test creating LinkedIn job posting"""
        create_job = input("Do you want to create a LinkedIn job posting? (yes/no): ").strip().lower()
        if create_job != 'yes':
            self.skipTest("Skipping LinkedIn job posting creation test.")
        
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            self.skipTest("No account ID provided. Skipping LinkedIn job posting creation test.")
        
        title = input("Enter job title: ").strip()
        description = input("Enter job description: ").strip()
        location = input("Enter job location: ").strip()
        if not title or not description or not location:
            self.skipTest("Job title, description, and location are required. Skipping LinkedIn job posting creation test.")
        
        payload = {
            "job_title": title,
            "description": description,
            "location": location,
            "employment_status": "FULL_TIME",
            "company": "Lunyamwi"
        }
        
        response = requests.post(f"{self.url}/linkedin/accounts/{account_id}/jobs/", json=payload)
        if response.status_code not in [200, 201]:
            self.fail(f"Error creating LinkedIn job posting: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"LinkedIn Job Posting Created Response: {response.json()}")


    def test_linkedin_job_applicants(self):
        """Test fetching LinkedIn job applicants"""
        account_id = os.getenv("LINKEDIN_TEST_ACCOUNT_ID", "")
        if not account_id:
            self.skipTest("No account ID provided. Skipping LinkedIn job applicants test.")
        
        job_id = input("Enter LinkedIn job ID to get applicants: ").strip()
        if not job_id:
            self.skipTest("No job ID provided. Skipping LinkedIn job applicants test.")
        
        response = requests.get(f"{self.url}/linkedin/accounts/{account_id}/jobs/{job_id}/applicants/")
        if response.status_code != 200:
            self.fail(f"Error fetching LinkedIn job applicants: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"LinkedIn Job Applicants Response: {response.json()}")

    
    