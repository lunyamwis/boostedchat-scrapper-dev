from django.test import TestCase
import requests
import logging
import os
from urllib.parse import unquote
from api.gmail.utils import get_google_oauth_url, exchange_code_for_tokens, extract_code_from_url

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GmailTests(TestCase):
    url = os.getenv("API_URL", "")

    def test_gmail_auth_url(self):
        """Test getting Gmail OAuth authorization URL"""
        get_auth_url = input("Do you want to test getting Gmail OAuth URL? (yes/no): ").strip().lower()
        if get_auth_url != 'yes':
            self.skipTest("Skipping Gmail auth URL test.")
        
        response = requests.get(f"{self.url}/gmail/auth/url/")
        if response.status_code != 200:
            self.fail(f"Error getting Gmail auth URL: {response.status_code} - {response.json()}")
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Validate response contains auth_url
        self.assertIn('auth_url', response_data)
        auth_url = response_data['auth_url']
        
        # Basic URL validation
        self.assertTrue(auth_url.startswith('https://accounts.google.com/o/oauth2/auth'))
        
        logger.info(f"Gmail Auth URL Response: {response_data}")
        
        # Display the URL for user
        print("\n" + "="*80)
        print("GMAIL OAUTH URL GENERATED")
        print("="*80)
        print(f"Authorization URL: {auth_url}")
        print("\nYou can use this URL to authorize Gmail access.")
        print("="*80)

    def test_gmail_oauth_callback_get(self):
        """Test Gmail OAuth callback GET method"""
        test_callback = input("Do you want to test Gmail OAuth callback (GET)? (yes/no): ").strip().lower()
        if test_callback != 'yes':
            self.skipTest("Skipping Gmail OAuth callback GET test.")
        
        # Get authorization code from user
        auth_code = input("Enter authorization code from OAuth callback: ").strip()
        if not auth_code:
            self.skipTest("No authorization code provided. Skipping Gmail OAuth callback test.")
        
        params = {'code': auth_code}
        
        response = requests.get(f"{self.url}/gmail/auth/callback/", params=params)
        if response.status_code != 200:
            try:
                error_details = response.json()
                self.fail(f"Error in Gmail OAuth callback: {response.status_code} - {error_details}")
            except:
                self.fail(f"Error in Gmail OAuth callback: {response.status_code} - {response.text}")
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Validate response contains tokens
        self.assertIn('access_token', response_data)
        logger.info(f"Gmail OAuth Callback GET Response: {response_data}")
        
        # Save tokens for account connection test
        access_token = response_data.get('access_token')
        refresh_token = response_data.get('refresh_token')
        
        print(f"\nTokens received:")
        print(f"Access Token: {access_token}")
        if refresh_token:
            print(f"Refresh Token: {refresh_token}")

        return response_data

    
    def test_gmail_account_connect(self):
        """Test connecting Gmail account"""
        connect_account = input("Do you want to test Gmail account connection? (yes/no): ").strip().lower()
        if connect_account != 'yes':
            self.skipTest("Skipping Gmail account connection test.")
        
        # Get tokens from environment or user input
        refresh_token = os.getenv("GMAIL_REFRESH_TOKEN", "")
        access_token = os.getenv("GMAIL_ACCESS_TOKEN", "")
        
        if not access_token:
            access_token = input("Enter Gmail access token: ").strip()
        if not refresh_token:
            refresh_token = input("Enter Gmail refresh token (optional): ").strip()
        
        if not access_token:
            self.skipTest("No access token provided. Skipping Gmail account connection test.")
        
        payload = {
            "provider": "GOOGLE_OAUTH",
            "access_token": access_token,
            "refresh_token": refresh_token
        }
        
        response = requests.post(f"{self.url}/gmail/accounts/", json=payload)
        if response.status_code not in [200, 201]:
            try:
                error_details = response.json()
                self.fail(f"Error connecting Gmail account: {response.status_code} - {error_details}")
            except:
                self.fail(f"Error connecting Gmail account: {response.status_code} - {response.text}")
        
        self.assertIn(response.status_code, [200, 201])
        response_data = response.json()
        logger.info(f"Gmail Account Connect Response: {response_data}")
        
        # Extract account ID if available
        if 'data' in response_data and isinstance(response_data['data'], dict):
            if 'account_id' in response_data['data']:
                account_id = response_data['data']['account_id']
                print(f"\nGmail Account Connected Successfully!")
                print(f"Account ID: {account_id}")
                print(f"Save this Account ID for future API calls.")
        
        return response_data

    def test_complete_gmail_oauth_flow(self):
        """Test complete Gmail OAuth flow from URL to account connection"""
        test_complete_flow = input("Do you want to test the complete Gmail OAuth flow? (yes/no): ").strip().lower()
        if test_complete_flow != 'yes':
            self.skipTest("Skipping complete Gmail OAuth flow test.")
        
        print("\n" + "="*80)
        print("COMPLETE GMAIL OAUTH FLOW TEST")
        print("="*80)
        
        # Step 1: Get OAuth URL
        print("Step 1: Getting OAuth authorization URL...")
        response = requests.get(f"{self.url}/gmail/auth/url/")
        if response.status_code != 200:
            self.fail(f"Failed to get OAuth URL: {response.status_code}")
        
        auth_url = response.json().get('auth_url')
        print(f"✓ OAuth URL generated")
        
        # Step 2: Display URL and get code
        print(f"\nStep 2: Please visit this URL to authorize:")
        print(f"{auth_url}")
        print(f"\nAfter authorization, copy the authorization code from the callback URL")
        
        auth_code = input("\nEnter the authorization code: ").strip()
        if not auth_code:
            self.skipTest("No authorization code provided.")
        
        # Step 3: Exchange code for tokens
        print("\nStep 3: Exchanging code for tokens...")
        payload = {'code': auth_code}
        response = requests.post(f"{self.url}/gmail/auth/callback/", json=payload)
        if response.status_code != 200:
            self.fail(f"Failed to exchange code for tokens: {response.status_code}")
        
        tokens = response.json()
        access_token = tokens.get('access_token')
        refresh_token = tokens.get('refresh_token')
        print(f"✓ Tokens received")
        
        # Step 4: Connect account
        print("\nStep 4: Connecting Gmail account...")
        payload = {
            "provider": "GOOGLE_OAUTH",
            "access_token": access_token,
            "refresh_token": refresh_token
        }
        
        response = requests.post(f"{self.url}/gmail/accounts/", json=payload)
        if response.status_code not in [200, 201]:
            self.fail(f"Failed to connect account: {response.status_code}")
        
        account_data = response.json()
        print(f"✓ Gmail account connected successfully")
        
        # Display results
        print("\n" + "="*80)
        print("OAUTH FLOW COMPLETED SUCCESSFULLY")
        print("="*80)
        print(f"Access Token: {access_token[:20]}...")
        if refresh_token:
            print(f"Refresh Token: {refresh_token[:20]}...")
        
        if 'data' in account_data and 'account_id' in account_data['data']:
            account_id = account_data['data']['account_id']
            print(f"Account ID: {account_id}")
        
        print("="*80)
        
        logger.info(f"Complete OAuth flow successful: {account_data}")

    def test_gmail_connect_accounts_connection_with_oauth(self):
        """Complete Gmail account connection flow"""
        connect_or_not = input("Do you want to connect a Gmail account? (y/n): ").strip().lower()
        if connect_or_not != 'y':
            self.skipTest("Skipping Gmail account connection test.")

        if connect_or_not == 'y':
            logger.info("No existing tokens found. Starting OAuth flow...")
            
            # Get OAuth credentials
            client_id = os.getenv("GMAIL_CLIENT_ID", "")
            client_secret = os.getenv("GMAIL_CLIENT_SECRET", "")
            redirect_uri = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:8000/auth/callback")

            if not client_id:
                client_id = input("Enter Google Client ID: ").strip()
            if not client_secret:
                client_secret = input("Enter Google Client Secret: ").strip()
            if not redirect_uri:
                redirect_uri = input("Enter Redirect URI (default: http://localhost:8000/auth/callback): ").strip()
                if not redirect_uri:
                    redirect_uri = "http://localhost:8000/auth/callback"

            if not client_id or not client_secret:
                self.skipTest("Missing OAuth credentials. Skipping Gmail connection test.")

            # Generate OAuth URL
            oauth_url = get_google_oauth_url(client_id, redirect_uri)
            logger.info(f"OAuth URL generated: {oauth_url}")
            
            print("\n" + "="*80)
            print("GMAIL OAUTH SETUP")
            print("="*80)
            print("1. Copy the URL below and open it in your browser:")
            print(f"\n{oauth_url}\n")
            print("2. Complete the authorization process")
            print("3. After authorization, you'll be redirected to a callback URL")
            print("4. Copy the ENTIRE callback URL from your browser's address bar")
            print("="*80)

            # Get callback URL from user
            callback_url = input("\nPaste the complete callback URL here: ").strip()
            if not callback_url:
                self.skipTest("No callback URL provided. Skipping Gmail connection test.")

            # Extract authorization code from URL
            try:
                auth_code = extract_code_from_url(callback_url)
                logger.info("Successfully extracted authorization code from callback URL")
            except Exception as e:
                # Fallback: ask user to manually enter the code
                logger.warning(f"Could not extract code from URL: {str(e)}")
                print("\nCould not automatically extract the authorization code.")
                auth_code = input("Please manually enter the authorization code: ").strip()
                if not auth_code:
                    self.skipTest("No authorization code provided. Skipping Gmail connection test.")

            # Handle URL-encoded code
            try:
                decoded_code = unquote(auth_code)
                if decoded_code != auth_code:
                    logger.info("Authorization code was URL-encoded. Using decoded version.")
                    auth_code = decoded_code
            except Exception as e:
                logger.warning(f"Could not decode authorization code: {e}")

            # Exchange code for tokens
            logger.info("Exchanging authorization code for tokens...")
            try:
                token_response = exchange_code_for_tokens(client_id, client_secret, auth_code, redirect_uri)
                
                if 'error' in token_response:
                    self.fail(f"Token exchange failed: {token_response.get('error_description', token_response.get('error'))}")
                
                refresh_token = token_response.get('refresh_token', '')
                access_token = token_response.get('access_token', '')
                
                if not access_token:
                    self.fail("No access token received from Google OAuth")
                
                logger.info("Successfully obtained tokens from Google OAuth")
                logger.info(f"Access token: {access_token[:20]}...")
                if refresh_token:
                    logger.info(f"Refresh token: {refresh_token[:20]}...")
                else:
                    logger.warning("No refresh token received. You may need to revoke access and re-authorize.")

                # Save tokens to environment for future use (optional)
                print(f"\nOptional: Save these tokens to your environment variables:")
                print(f"GMAIL_ACCESS_TOKEN={access_token}")
                if refresh_token:
                    print(f"GMAIL_REFRESH_TOKEN={refresh_token}")

                payload = {
                    "provider": "GOOGLE_OAUTH",
                    "refresh_token": refresh_token,
                    "access_token": access_token
                }

            except Exception as e:
                self.fail(f"Error during token exchange: {str(e)}")

        # Connect Gmail account using the API
        logger.info("Connecting Gmail account...")
        try:
            response = requests.post(f"{self.url}/gmail/accounts/", json=payload)
            logger.info(f"Gmail connection response status: {response.status_code}")
            
            if response.status_code not in [200, 201]:
                error_message = f"Failed to connect Gmail account: {response.status_code}"
                try:
                    error_details = response.json()
                    error_message += f" - {error_details}"
                except:
                    error_message += f" - {response.text}"
                self.fail(error_message)
            
            self.assertIn(response.status_code, [200, 201])
            response_data = response.json()
            logger.info(f"Gmail account connected successfully: {response_data}")
            
            # Extract account ID for future tests
            if 'data' in response_data and 'account_id' in response_data['data']:
                account_id = response_data['data']['account_id']
                logger.info(f"Gmail Account ID: {account_id}")
                print(f"\nSave this Account ID for future tests: {account_id}")
            
        except requests.exceptions.RequestException as e:
            self.fail(f"Network error during Gmail connection: {str(e)}")
        except Exception as e:
            self.fail(f"Unexpected error during Gmail connection: {str(e)}")


    def test_gmail_account_reconnect(self):
        """Test reconnecting Gmail account with new tokens"""
        reconnect = input("Do you want to test Gmail account reconnect? (yes/no): ").strip().lower()
        if reconnect != 'yes':
            self.skipTest("Skipping Gmail account reconnect test.")
        
        account_id = os.getenv("GMAIL_ACCOUNT_ID")
        if not account_id:
            self.skipTest("No account ID provided. Skipping Gmail reconnect test.")
        
        refresh_token = input("Enter new refresh token: ").strip()
        access_token = input("Enter new access token: ").strip()
        
        if not refresh_token and not access_token:
            self.skipTest("No tokens provided. Skipping Gmail reconnect test.")
        
        payload = {
            "refresh_token": refresh_token,
            "access_token": access_token
        }
        
        response = requests.post(f"{self.url}/gmail/accounts/{account_id}/reconnect/", json=payload)
        if response.status_code not in [200, 201]:
            self.fail(f"Error reconnecting Gmail account: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"Gmail Account Reconnect Response: {response.json()}")

    def test_gmail_emails_list(self):
        """Test listing Gmail emails"""
        account_id = os.getenv("GMAIL_ACCOUNT_ID")
        if not account_id:
            self.skipTest("No account ID provided. Skipping Gmail emails list test.")
        
        params = {
            'limit': '10',
            'folder': 'INBOX',
            'unread_only': 'false'
        }
        
        response = requests.get(f"{self.url}/gmail/accounts/{account_id}/emails/", params=params)
        if response.status_code != 200:
            self.fail(f"Error listing Gmail emails: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Gmail Emails List Response: {response.json()}")

    def test_gmail_send_email(self):
        """Test sending Gmail email"""
        send_email = input("Do you want to test sending a Gmail email? (yes/no): ").strip().lower()
        if send_email != 'yes':
            self.skipTest("Skipping Gmail send email test.")
        
        account_id = os.getenv("GMAIL_ACCOUNT_ID")
        if not account_id:
            self.skipTest("No account ID provided. Skipping Gmail send email test.")
        
        to_email = input("Enter recipient email address: ").strip()
        if not to_email:
            self.skipTest("No recipient email provided. Skipping Gmail send email test.")
        
        subject = input("Enter email subject: ").strip()
        if not subject:
            subject = "Test Email from API"
        
        body = input("Enter email body: ").strip()
        if not body:
            body = "This is a test email sent via the Gmail API."
        
        payload = {
            "to": eval(to_email),
            "subject": subject,
            "body": body,
            "body_type": "html"
        }
        
        response = requests.post(f"{self.url}/gmail/accounts/{account_id}/emails/", json=payload)
        if response.status_code not in [200, 201]:
            self.fail(f"Error sending Gmail email: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"Gmail Send Email Response: {response.json()}")

    def test_gmail_email_get(self):
        """Test getting specific Gmail email"""
        account_id = os.getenv("GMAIL_ACCOUNT_ID")
        if not account_id:
            self.skipTest("No account ID provided. Skipping Gmail email get test.")
        
        email_id = input("Enter Gmail email ID: ").strip()
        if not email_id:
            self.skipTest("No email ID provided. Skipping Gmail email get test.")
        
        params = {
            'include_thread': 'false',
            'include_attachments': 'true',
            'mark_as_read': 'false'
        }
        
        response = requests.get(f"{self.url}/gmail/accounts/{account_id}/emails/{email_id}/", params=params)
        if response.status_code != 200:
            self.fail(f"Error getting Gmail email: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Gmail Email Get Response: {response.json()}")

    def test_gmail_email_update(self):
        """Test updating Gmail email"""
        update_email = input("Do you want to test updating a Gmail email? (yes/no): ").strip().lower()
        if update_email != 'yes':
            self.skipTest("Skipping Gmail email update test.")
        
        account_id = os.getenv("GMAIL_ACCOUNT_ID")
        if not account_id:
            self.skipTest("No account ID provided. Skipping Gmail email update test.")
        
        email_id = input("Enter Gmail email ID to update: ").strip()
        if not email_id:
            self.skipTest("No email ID provided. Skipping Gmail email update test.")
        
        is_read = input("Mark as read? (true/false): ").strip().lower()
        is_starred = input("Mark as starred? (true/false): ").strip().lower()
        
        payload = {}
        if is_read in ['true', 'false']:
            payload['is_read'] = is_read == 'true'
        if is_starred in ['true', 'false']:
            payload['is_starred'] = is_starred == 'true'
        
        if not payload:
            payload = {'is_read': True}  # Default action
        
        response = requests.put(f"{self.url}/gmail/accounts/{account_id}/emails/{email_id}/", json=payload)
        if response.status_code not in [200, 201]:
            self.fail(f"Error updating Gmail email: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"Gmail Email Update Response: {response.json()}")

    def test_gmail_email_delete(self):
        """Test deleting Gmail email"""
        delete_email = input("Do you want to test deleting a Gmail email? (yes/no): ").strip().lower()
        if delete_email != 'yes':
            self.skipTest("Skipping Gmail email delete test.")
        
        account_id = os.getenv("GMAIL_ACCOUNT_ID")
        if not account_id:
            self.skipTest("No account ID provided. Skipping Gmail email delete test.")
        
        email_id = input("Enter Gmail email ID to delete: ").strip()
        if not email_id:
            self.skipTest("No email ID provided. Skipping Gmail email delete test.")
        
        permanent = input("Permanent delete? (true/false, default: false): ").strip().lower()
        if permanent not in ['true', 'false']:
            permanent = 'false'
        
        params = {'permanent': permanent}
        
        response = requests.delete(f"{self.url}/gmail/accounts/{account_id}/emails/{email_id}/", params=params)
        if response.status_code not in [200, 204]:
            self.fail(f"Error deleting Gmail email: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 204])
        logger.info(f"Gmail Email Delete Response: {response.status_code}")

    def test_gmail_retrieve_attachment(self):
        """Test retrieving Gmail email attachment"""
        account_id = os.getenv("GMAIL_ACCOUNT_ID")
        if not account_id:
            self.skipTest("No account ID provided. Skipping Gmail attachment test.")
        
        email_id = input("Enter Gmail email ID: ").strip()
        if not email_id:
            self.skipTest("No email ID provided. Skipping Gmail attachment test.")
        
        attachment_id = input("Enter attachment ID: ").strip()
        if not attachment_id:
            self.skipTest("No attachment ID provided. Skipping Gmail attachment test.")
        
        response = requests.get(f"{self.url}/gmail/accounts/{account_id}/emails/{email_id}/attachments/{attachment_id}/")
        if response.status_code != 200:
            self.fail(f"Error retrieving Gmail attachment: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Gmail Attachment Response: {response.status_code} - Content length: {len(response.content)}")

    def test_gmail_list_folders(self):
        """Test listing Gmail folders/labels"""
        account_id = os.getenv("GMAIL_ACCOUNT_ID")
        if not account_id:
            self.skipTest("No account ID provided. Skipping Gmail folders list test.")
        
        response = requests.get(f"{self.url}/gmail/accounts/{account_id}/folders/")
        if response.status_code != 200:
            self.fail(f"Error listing Gmail folders: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Gmail Folders List Response: {response.json()}")

    def test_gmail_folder_details(self):
        """Test getting Gmail folder details"""
        account_id = os.getenv("GMAIL_ACCOUNT_ID")
        if not account_id:
            self.skipTest("No account ID provided. Skipping Gmail folder details test.")
        
        folder_id = input("Enter Gmail folder/label ID: ").strip()
        if not folder_id:
            self.skipTest("No folder ID provided. Skipping Gmail folder details test.")
        
        response = requests.get(f"{self.url}/gmail/accounts/{account_id}/folders/{folder_id}/")
        if response.status_code != 200:
            self.fail(f"Error getting Gmail folder details: {response.status_code} - {response.json()}")
        self.assertEqual(response.status_code, 200)
        logger.info(f"Gmail Folder Details Response: {response.json()}")

    def test_gmail_create_draft(self):
        """Test creating Gmail draft"""
        create_draft = input("Do you want to test creating a Gmail draft? (yes/no): ").strip().lower()
        if create_draft != 'yes':
            self.skipTest("Skipping Gmail create draft test.")
        
        account_id = os.getenv("GMAIL_ACCOUNT_ID")
        if not account_id:
            self.skipTest("No account ID provided. Skipping Gmail create draft test.")
        
        to_email = input("Enter recipient email address: ").strip()
        if not to_email:
            self.skipTest("No recipient email provided. Skipping Gmail create draft test.")
        
        subject = input("Enter draft subject: ").strip()
        if not subject:
            subject = "Draft Email"
        
        body = input("Enter draft body: ").strip()
        if not body:
            body = "This is a draft email created via the Gmail API."
        
        payload = {
            "to_email": to_email,
            "subject": subject,
            "body": body
        }
        
        response = requests.post(f"{self.url}/gmail/accounts/{account_id}/drafts/", json=payload)
        if response.status_code not in [200, 201]:
            self.fail(f"Error creating Gmail draft: {response.status_code} - {response.json()}")
        self.assertIn(response.status_code, [200, 201])
        logger.info(f"Gmail Create Draft Response: {response.json()}")

    