from django.test import TestCase
import requests
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhatsAppAPITests(TestCase):
    url = os.getenv("API_URL", "")

    def test_authurl(self):
        """Test WhatsApp auth URL"""
        response = requests.get(f"{self.url}/whatsapp/auth/")
        if response.status_code != 200:
            self.fail(f"Error getting auth URL: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Auth URL Response: {response.json()}")

    def test_oauth_callback(self):
        """Test WhatsApp OAuth callback"""
        code = input("Enter the OAuth code from the redirect URL: ").strip()
        if not code:
            self.skipTest("No OAuth code provided. Skipping OAuth callback test.")
        
        params = {"code": code}
        response = requests.get(f"{self.url}/whatsapp/oauth/callback/", params=params)
        if response.status_code != 200:
            self.fail(f"Error in OAuth callback: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"OAuth Callback Response: {response.json()}")


    def test_user_login(self):
        """Test WhatsApp user login"""
        test_login = input("Do you want to test WhatsApp user login? (yes/no): ").strip().lower()
        if test_login != 'yes':
            self.skipTest("Skipping WhatsApp user login test.")
        
        response = requests.get(f"{self.url}/whatsapp/whapi/users/login/")
        if response.status_code not in [200, 201]:
            self.fail(f"Error in user login: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"User Login Response: {response.json()}")

    
    def test_user_logout(self):
        """Test WhatsApp user logout"""
        test_logout = input("Do you want to test WhatsApp user logout? (yes/no): ").strip().lower()
        if test_logout != 'yes':
            self.skipTest("Skipping WhatsApp user logout test.")
        
        response = requests.post(f"{self.url}/whatsapp/whapi/users/logout/")
        if response.status_code not in [200, 201]:
            self.fail(f"Error in user logout: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"User Logout Response: {response.json()}")

    def test_user_profile(self):
        """Test WhatsApp user profile"""
        response = requests.get(f"{self.url}/whatsapp/whapi/users/profile/")
        if response.status_code != 200:
            self.fail(f"Error getting user profile: {response.status_code} - {response.json()}")
        print(response.json())
        self.assertEqual(response.status_code, 200)

        logger.info(f"User Profile Response: {response.json()}")

    def test_user_info(self):
        """Test WhatsApp user info"""
        contact_id = input("Enter contact ID for profile (or leave blank to skip): ").strip()
        if not contact_id:
            self.skipTest("No contact ID provided. Skipping user profile test.")

        payload = {"contact_id": contact_id}
        response = requests.post(f"{self.url}/whatsapp/whapi/users/info/", json=payload)
        if response.status_code != 200:
            self.fail(f"Error getting user info: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"User Info Response: {response.json()}")

    def test_user_gdpr(self):
        """Test WhatsApp user GDPR"""
        response = requests.get(f"{self.url}/whatsapp/whapi/users/gdpr/")
        if response.status_code != 200:
            self.fail(f"Error getting user GDPR: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"User GDPR Response: {response.json()}")

    def test_user_status(self):
        """Test WhatsApp user status"""
        payload = {"status": "Jesus is the Saviour of the world!"}
        response = requests.put(f"{self.url}/whatsapp/whapi/status/", json=payload)
        if response.status_code != 200:
            self.fail(f"Error getting user status: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"User Status Response: {response.json()}")

    def test_messages_list(self):
        """Test WhatsApp messages list"""
        response = requests.get(f"{self.url}/whatsapp/whapi/messages/list/")
        if response.status_code != 200:
            self.fail(f"Error getting messages list: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Messages List Response: {response.json()}")

    def test_messages_list_by_chat(self):
        """Test WhatsApp messages list by chat"""
        chat_id = input("Enter chat ID for messages (or leave blank to skip): ").strip()
        if not chat_id:
            self.skipTest("No chat ID provided. Skipping messages list by chat test.")
        
        response = requests.get(f"{self.url}/whatsapp/whapi/messages/list/{chat_id}/")
        if response.status_code != 200:
            self.fail(f"Error getting messages by chat: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Messages List by Chat Response: {response.json()}")

    def test_send_text_message(self):
        """Test sending WhatsApp text message"""
        send_text = input("Do you want to test sending a text message? (yes/no): ").strip().lower()
        if send_text != 'yes':
            self.skipTest("Skipping send text message test.")
        
        to_number = input("Enter recipient phone number: ").strip()
        if not to_number:
            self.skipTest("No recipient number provided.")
        
        message_text = input("Enter message text: ").strip()
        if not message_text:
            message_text = "Test message from API"
        
        payload = {
            "to": to_number,
            "body": message_text
        }
        
        response = requests.post(f"{self.url}/whatsapp/whapi/messages/text/", json=payload)
        if response.status_code not in [200, 201]:
            self.fail(f"Error sending text message: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"Send Text Message Response: {response.json()}")

    def test_send_image_message(self):
        """Test sending WhatsApp image message"""
        send_image = input("Do you want to test sending an image message? (yes/no): ").strip().lower()
        if send_image != 'yes':
            self.skipTest("Skipping send image message test.")
        
        to_number = input("Enter recipient phone number: ").strip()
        if not to_number:
            self.skipTest("No recipient number provided.")
        
        image_url = input("Enter image URL: ").strip()
        if not image_url:
            self.skipTest("No image URL provided.")
        
        payload = {
            "to": to_number,
            "media": image_url,
            "caption": "Test image from API"
        }
        
        response = requests.post(f"{self.url}/whatsapp/whapi/messages/image/", json=payload)
        if response.status_code not in [200, 201]:
            self.fail(f"Error sending image message: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"Send Image Message Response: {response.json()}")

    def test_send_video_message(self):
        """Test sending WhatsApp video message"""
        send_video = input("Do you want to test sending a video message? (yes/no): ").strip().lower()
        if send_video != 'yes':
            self.skipTest("Skipping send video message test.")
        
        to_number = input("Enter recipient phone number: ").strip()
        if not to_number:
            self.skipTest("No recipient number provided.")
        
        video_url = input("Enter video URL: ").strip()
        if not video_url:
            self.skipTest("No video URL provided.")
        
        payload = {
            "to": to_number,
            "media": video_url,
            "caption": "Test video from API"
        }
        
        response = requests.post(f"{self.url}/whatsapp/whapi/messages/video/", json=payload)
        if response.status_code not in [200, 201]:
            self.fail(f"Error sending video message: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"Send Video Message Response: {response.json()}")

    def test_send_document_message(self):
        """Test sending WhatsApp document message"""
        send_doc = input("Do you want to test sending a document message? (yes/no): ").strip().lower()
        if send_doc != 'yes':
            self.skipTest("Skipping send document message test.")
        
        to_number = input("Enter recipient phone number: ").strip()
        if not to_number:
            self.skipTest("No recipient number provided.")
        
        doc_url = input("Enter document URL: ").strip()
        if not doc_url:
            self.skipTest("No document URL provided.")
        
        payload = {
            "to": to_number,
            "media": doc_url,
            "filename": "test_document.pdf"
        }
        
        response = requests.post(f"{self.url}/whatsapp/whapi/messages/document/", json=payload)
        if response.status_code not in [200, 201]:
            self.fail(f"Error sending document message: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"Send Document Message Response: {response.json()}")

    def test_send_location_message(self):
        """Test sending WhatsApp location message"""
        send_location = input("Do you want to test sending a location message? (yes/no): ").strip().lower()
        if send_location != 'yes':
            self.skipTest("Skipping send location message test.")
        
        to_number = input("Enter recipient phone number: ").strip()
        if not to_number:
            self.skipTest("No recipient number provided.")
        
        payload = {
            "to": to_number,
            "latitude": float("40.7128"),
            "longitude": float("-74.0060"),
            "name": "New York City",
            "address": "New York, NY, USA"
        }
        
        response = requests.post(f"{self.url}/whatsapp/whapi/messages/location/", json=payload)
        if response.status_code not in [200, 201]:
            self.fail(f"Error sending location message: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"Send Location Message Response: {response.json()}")

    def test_send_contact_message(self):
        """Test sending WhatsApp contact message"""
        send_contact = input("Do you want to test sending a contact message? (yes/no): ").strip().lower()
        if send_contact != 'yes':
            self.skipTest("Skipping send contact message test.")
        
        to_number = input("Enter recipient phone number: ").strip()
        if not to_number:
            self.skipTest("No recipient number provided.")
        
        payload = {
            "to": to_number,
            "name":"VROMI",
            "vcard": "BEGIN:VCARD\nVERSION:3.0\nFN:John Doe\nTEL;TYPE=CELL:+1234567890\nEMAIL;TYPE=WORK:john.doe@example.com\nEND:VCARD"
        }
        
        response = requests.post(f"{self.url}/whatsapp/whapi/messages/contact/", json=payload)
        if response.status_code not in [200, 201]:
            self.fail(f"Error sending contact message: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"Send Contact Message Response: {response.json()}")

    def test_send_poll_message(self):
        """Test sending WhatsApp poll message"""
        send_poll = input("Do you want to test sending a poll message? (yes/no): ").strip().lower()
        if send_poll != 'yes':
            self.skipTest("Skipping send poll message test.")
        
        to_number = input("Enter recipient phone number: ").strip()
        if not to_number:
            self.skipTest("No recipient number provided.")
        
        payload = {
            "to": to_number,
            "title": "Favorite Color Poll",
            "name": "What's your favorite color?",
            "options": ["Red", "Blue", "Green", "Yellow"],
            "count": 1
        }
        
        response = requests.post(f"{self.url}/whatsapp/whapi/messages/poll/", json=payload)
        if response.status_code not in [200, 201]:
            self.fail(f"Error sending poll message: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"Send Poll Message Response: {response.json()}")

    def test_message_detail(self):
        """Test getting WhatsApp message details"""
        message_id = input("Enter message ID for details (or leave blank to skip): ").strip()
        if not message_id:
            self.skipTest("No message ID provided. Skipping message detail test.")
        
        response = requests.get(f"{self.url}/whatsapp/whapi/messages/{message_id}/")
        if response.status_code != 200:
            self.fail(f"Error getting message details: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Message Detail Response: {response.json()}")

    def test_message_reaction(self):
        """Test WhatsApp message reaction"""
        react_message = input("Do you want to test message reaction? (yes/no): ").strip().lower()
        if react_message != 'yes':
            self.skipTest("Skipping message reaction test.")
        
        message_id = input("Enter message ID to react to: ").strip()
        if not message_id:
            self.skipTest("No message ID provided.")
        
        emoji = input("Enter emoji reaction (or leave blank for 👍): ").strip()
        if not emoji:
            emoji = "👍"
        
        payload = {"emoji": emoji}
        
        response = requests.put(f"{self.url}/whatsapp/whapi/messages/{message_id}/reaction/", json=payload)
        if response.status_code not in [200, 201]:
            self.fail(f"Error reacting to message: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"Message Reaction Response: {response.json()}")

    def test_chats_list(self):
        """Test WhatsApp chats list"""
        response = requests.get(f"{self.url}/whatsapp/whapi/chats/")
        if response.status_code != 200:
            self.fail(f"Error getting chats list: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Chats List Response: {response.json()}")

    def test_chat_detail(self):
        """Test WhatsApp chat details"""
        chat_id = input("Enter chat ID for details (or leave blank to skip): ").strip()
        if not chat_id:
            self.skipTest("No chat ID provided. Skipping chat detail test.")
        
        response = requests.get(f"{self.url}/whatsapp/whapi/chats/{chat_id}/")
        if response.status_code != 200:
            self.fail(f"Error getting chat details: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Chat Detail Response: {response.json()}")

    def test_contacts_list(self):
        """Test WhatsApp contacts list"""
        response = requests.get(f"{self.url}/whatsapp/whapi/contacts/")
        if response.status_code != 200:
            self.fail(f"Error getting contacts list: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Contacts List Response: {response.json()}")

    def test_contact_detail(self):
        """Test WhatsApp contact details"""
        contact_id = input("Enter contact ID for details (or leave blank to skip): ").strip()
        if not contact_id:
            self.skipTest("No contact ID provided. Skipping contact detail test.")
        
        response = requests.get(f"{self.url}/whatsapp/whapi/contacts/{contact_id}/")
        if response.status_code != 200:
            self.fail(f"Error getting contact details: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Contact Detail Response: {response.json()}")

    def test_groups_list(self):
        """Test WhatsApp groups list"""
        response = requests.get(f"{self.url}/whatsapp/whapi/groups/")
        if response.status_code != 200:
            self.fail(f"Error getting groups list: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Groups List Response: {response.json()}")

    def test_group_detail(self):
        """Test WhatsApp group details"""
        group_id = input("Enter group ID for details (or leave blank to skip): ").strip()
        if not group_id:
            self.skipTest("No group ID provided. Skipping group detail test.")
        
        response = requests.get(f"{self.url}/whatsapp/whapi/groups/{group_id}/")
        if response.status_code != 200:
            self.fail(f"Error getting group details: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Group Detail Response: {response.json()}")

    def test_stories_list(self):
        """Test WhatsApp stories list"""
        response = requests.get(f"{self.url}/whatsapp/whapi/stories/")
        if response.status_code != 200:
            self.fail(f"Error getting stories list: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Stories List Response: {response.json()}")

    def test_newsletters_list(self):
        """Test WhatsApp newsletters list"""
        response = requests.get(f"{self.url}/whatsapp/whapi/newsletters/")
        if response.status_code != 200:
            self.fail(f"Error getting newsletters list: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Newsletters List Response: {response.json()}")

    def test_business_info(self):
        """Test WhatsApp business info"""
        response = requests.get(f"{self.url}/whatsapp/whapi/business/")
        if response.status_code != 200:
            self.fail(f"Error getting business info: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Business Info Response: {response.json()}")

    def test_business_products(self):
        """Test WhatsApp business products"""
        response = requests.get(f"{self.url}/whatsapp/whapi/business/products/")
        if response.status_code != 200:
            self.fail(f"Error getting business products: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Business Products Response: {response.json()}")

    def test_labels_list(self):
        """Test WhatsApp labels list"""
        response = requests.get(f"{self.url}/whatsapp/whapi/labels/")
        if response.status_code != 200:
            self.fail(f"Error getting labels list: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Labels List Response: {response.json()}")

    def test_blacklist(self):
        """Test WhatsApp blacklist"""
        response = requests.get(f"{self.url}/whatsapp/whapi/blacklist/")
        if response.status_code != 200:
            self.fail(f"Error getting blacklist: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Blacklist Response: {response.json()}")

    def test_communities_list(self):
        """Test WhatsApp communities list"""
        response = requests.get(f"{self.url}/whatsapp/whapi/communities/")
        if response.status_code != 200:
            self.fail(f"Error getting communities list: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Communities List Response: {response.json()}")

    def test_calls(self):
        """Test WhatsApp calls list"""
        start_time = input("Enter start time for calls (or leave blank to use current time): ").strip()
        if not start_time:  
            import time
            start_time = int(time.time())+50
        else:
            try:
                start_time = int(start_time)
            except ValueError:
                self.skipTest("Invalid start time provided. Skipping calls test.")
        payload = {"start_time": str(start_time)}
        response = requests.post(f"{self.url}/whatsapp/whapi/calls/", json=payload)
        if response.status_code != 200:
            self.fail(f"Error getting calls list: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Calls List Response: {response.json()}")

    def test_media_upload(self):
        """Test WhatsApp media upload"""
        upload_media = input("Do you want to test media upload? (yes/no): ").strip().lower()
        if upload_media != 'yes':
            self.skipTest("Skipping media upload test.")
        
        media_url = input("Enter media URL to upload: ").strip()
        if not media_url:
            self.skipTest("No media URL provided.")
        
        payload = {"media": media_url}
        
        response = requests.post(f"{self.url}/whatsapp/whapi/media/", json=payload)
        if response.status_code not in [200, 201]:
            self.fail(f"Error uploading media: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"Media Upload Response: {response.json()}")