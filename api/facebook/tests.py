from django.test import TestCase
import requests
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FacebookAPITests(TestCase):
    url = os.getenv("API_URL", "")

    def test_facebook_auth_url(self):
        """Test Facebook auth URL endpoint"""
        response = requests.get(f"{self.url}/facebook/auth/")
        if response.status_code != 200:
            self.fail(f"Error getting auth URL: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        print(f"Visit this URL to authenticate: {response.json().get('auth_url')}")
        logger.info(f"Facebook Auth URL Response: {response.json()}")

    def test_facebook_auth_callback(self):
        """Test Facebook auth callback endpoint"""
        code = input("Enter the Facebook auth code from the URL after login: ").strip()
        if not code:
            self.skipTest("No auth code provided.")
        
        response = requests.get(f"{self.url}/facebook/auth/callback/", params={"code": code})
        if response.status_code != 200:
            self.fail(f"Error in auth callback: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Facebook Auth Callback Response: {response.json()}")

    def test_facebook_messenger_profile(self):
        """Test Facebook messenger profile endpoint"""
        response = requests.get(f"{self.url}/facebook/messenger-profile/")
        if response.status_code != 200:
            self.fail(f"Error getting messenger profile: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Facebook Messenger Profile Response: {response.json()}")

    
    def test_facebook_user_me(self):
        """Test Facebook user me endpoint"""
        response = requests.get(f"{self.url}/facebook/users/me/")
        if response.status_code != 200:
            self.fail(f"Error getting user me: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Facebook User Me Response: {response.json()}")

    
    def test_facebook_send_message(self):
        """Test sending Facebook message"""
        send_message = input("Do you want to test sending a Facebook message? (yes/no): ").strip().lower()
        if send_message != 'yes':
            self.skipTest("Skipping Facebook send message test.")
        
        recipient_id = input("Enter recipient ID: ").strip()
        if not recipient_id:
            self.skipTest("No recipient ID provided.")
        
        message_text = input("Enter message text: ").strip()
        if not message_text:
            message_text = "Test message from API"
        
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
        
        response = requests.post(f"{self.url}/facebook/messages/", json=payload)
        if response.status_code not in [200, 201]:
            self.fail(f"Error sending message: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"Facebook Send Message Response: {response.json()}")

    
    def test_facebook_batch_request(self):
        """Test Facebook batch request"""
        test_batch = input("Do you want to test Facebook batch request? (yes/no): ").strip().lower()
        if test_batch != 'yes':
            self.skipTest("Skipping Facebook batch request test.")
        
        payload = {
            "batch": [
                {
                    "method": "GET",
                    "relative_url": "me"
                },
                {
                    "method": "GET", 
                    "relative_url": "me/accounts"
                }
            ]
        }
        
        response = requests.post(f"{self.url}/facebook/batch/", json=payload)
        if response.status_code not in [200, 201]:
            self.fail(f"Error in batch request: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"Facebook Batch Request Response: {response.json()}")

    def test_facebook_page_posts_with_id(self):
        """Test Facebook page posts with page ID"""
        page_id = input("Enter Facebook page ID for posts (or leave blank to skip): ").strip()
        if not page_id:
            self.skipTest("No page ID provided. Skipping page posts test.")
        
        response = requests.get(f"{self.url}/facebook/pages/{page_id}/posts/")
        if response.status_code != 200:
            self.fail(f"Error getting page posts: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Facebook Page Posts Response: {response.json()}")

    def test_facebook_page_insights_with_id(self):
        """Test Facebook page insights with page ID"""
        page_id = input("Enter Facebook page ID for insights (or leave blank to skip): ").strip()
        if not page_id:
            self.skipTest("No page ID provided. Skipping page insights test.")
        
        response = requests.get(f"{self.url}/facebook/pages/{page_id}/insights/")
        if response.status_code != 200:
            self.fail(f"Error getting page insights: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Facebook Page Insights Response: {response.json()}")

    def test_facebook_page_conversations_with_id(self):
        """Test Facebook page conversations with page ID"""
        page_id = input("Enter Facebook page ID for conversations (or leave blank to skip): ").strip()
        if not page_id:
            self.skipTest("No page ID provided. Skipping page conversations test.")
        
        response = requests.get(f"{self.url}/facebook/pages/{page_id}/conversations/")
        if response.status_code != 200:
            self.fail(f"Error getting page conversations: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Facebook Page Conversations Response: {response.json()}")

    def test_facebook_create_post(self):
        """Test creating Facebook post"""
        create_post = input("Do you want to test creating a Facebook post? (yes/no): ").strip().lower()
        if create_post != 'yes':
            self.skipTest("Skipping Facebook create post test.")
        
        page_id = input("Enter Facebook page ID for posting: ").strip()
        if not page_id:
            self.skipTest("No page ID provided.")
        
        message = input("Enter post message: ").strip()
        if not message:
            message = "Test post from API"
        
        payload = {"message": message}
        
        response = requests.post(f"{self.url}/facebook/pages/{page_id}/posts/", json=payload)
        if response.status_code not in [200, 201]:
            self.fail(f"Error creating post: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"Facebook Create Post Response: {response.json()}")

    def test_facebook_page_photos_with_id(self):
        """Test Facebook page photos with page ID"""
        page_id = input("Enter Facebook page ID for photos (or leave blank to skip): ").strip()
        if not page_id:
            self.skipTest("No page ID provided. Skipping page photos test.")
        
        response = requests.get(f"{self.url}/facebook/pages/{page_id}/photos/")
        if response.status_code != 200:
            self.fail(f"Error getting page photos: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Facebook Page Photos Response: {response.json()}")

    