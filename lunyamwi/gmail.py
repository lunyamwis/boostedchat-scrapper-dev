import requests
import logging
import os
from typing import Optional, Dict, Any, List, Union
from urllib.parse import unquote

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GmailAPIClient:
    """Gmail API client for managing Gmail accounts, emails, and OAuth authentication"""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("API_URL", "")
        if not self.base_url:
            raise ValueError("API_URL must be provided either as parameter or environment variable")
        self.account_id = None
    
    def set_account_id(self, account_id: str):
        """Set the default account ID for operations"""
        self.account_id = account_id
    
    # OAuth and Authentication Methods
    def get_oauth_url(self) -> Dict[str, Any]:
        """Get Gmail OAuth authorization URL"""
        try:
            response = requests.get(f"{self.base_url}/gmail/auth/url/")
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Gmail OAuth URL Response: {result}")
            
            # Validate response
            if 'auth_url' not in result:
                return {
                    "success": False,
                    "error": "No auth_url in response"
                }
            
            auth_url = result['auth_url']
            if not auth_url.startswith('https://accounts.google.com/o/oauth2/auth'):
                return {
                    "success": False,
                    "error": "Invalid OAuth URL format"
                }
            
            return {
                "success": True,
                "data": result,
                "auth_url": auth_url
            }
        except requests.RequestException as e:
            logger.error(f"Error getting Gmail OAuth URL: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def handle_oauth_callback_get(self, auth_code: str) -> Dict[str, Any]:
        """Handle Gmail OAuth callback with GET method"""
        if not auth_code:
            return {
                "success": False,
                "error": "Authorization code is required"
            }
        
        params = {'code': auth_code}
        
        try:
            response = requests.get(f"{self.base_url}/gmail/auth/callback/", params=params)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Gmail OAuth Callback GET Response: {result}")
            
            # Validate response contains tokens
            if 'access_token' not in result:
                return {
                    "success": False,
                    "error": "No access token in response"
                }
            
            return {
                "success": True,
                "data": result,
                "access_token": result.get('access_token'),
                "refresh_token": result.get('refresh_token')
            }
        except requests.RequestException as e:
            logger.error(f"Error in Gmail OAuth callback: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def handle_oauth_callback_post(self, auth_code: str) -> Dict[str, Any]:
        """Handle Gmail OAuth callback with POST method"""
        if not auth_code:
            return {
                "success": False,
                "error": "Authorization code is required"
            }
        
        payload = {'code': auth_code}
        
        try:
            response = requests.post(f"{self.base_url}/gmail/auth/callback/", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Gmail OAuth Callback POST Response: {result}")
            
            return {
                "success": True,
                "data": result,
                "access_token": result.get('access_token'),
                "refresh_token": result.get('refresh_token')
            }
        except requests.RequestException as e:
            logger.error(f"Error in Gmail OAuth callback POST: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    # Account Management Methods
    def connect_account(self, access_token: str, refresh_token: Optional[str] = None) -> Dict[str, Any]:
        """Connect Gmail account using OAuth tokens"""
        payload = {
            "provider": "GOOGLE_OAUTH",
            "access_token": access_token
        }
        
        if refresh_token:
            payload["refresh_token"] = refresh_token
        
        try:
            response = requests.post(f"{self.base_url}/gmail/accounts/", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Gmail Account Connect Response: {result}")
            
            # Extract and store account ID
            if 'data' in result and isinstance(result['data'], dict):
                if 'account_id' in result['data']:
                    self.account_id = result['data']['account_id']
                    logger.info(f"Account ID set to: {self.account_id}")
            
            return {
                "success": True,
                "data": result,
                "account_id": self.account_id
            }
        except requests.RequestException as e:
            logger.error(f"Error connecting Gmail account: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def reconnect_account(self, account_id: Optional[str] = None, access_token: Optional[str] = None, refresh_token: Optional[str] = None) -> Dict[str, Any]:
        """Reconnect Gmail account with new tokens"""
        account_id = account_id or self.account_id
        if not account_id:
            return {
                "success": False,
                "error": "Account ID is required"
            }
        
        payload = {}
        if access_token:
            payload["access_token"] = access_token
        if refresh_token:
            payload["refresh_token"] = refresh_token
        
        if not payload:
            return {
                "success": False,
                "error": "At least one token (access_token or refresh_token) is required"
            }
        
        try:
            response = requests.post(f"{self.base_url}/gmail/accounts/{account_id}/reconnect/", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Gmail Account Reconnect Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error reconnecting Gmail account: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    # Email Management Methods
    def list_emails(self, account_id: Optional[str] = None, limit: int = 10, folder: str = 'INBOX', unread_only: bool = False) -> Dict[str, Any]:
        """List Gmail emails"""
        account_id = account_id or self.account_id
        if not account_id:
            return {
                "success": False,
                "error": "Account ID is required"
            }
        
        params = {
            'limit': str(limit),
            'folder': folder,
            'unread_only': str(unread_only).lower()
        }
        
        try:
            response = requests.get(f"{self.base_url}/gmail/accounts/{account_id}/emails/", params=params)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Gmail Emails List Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error listing Gmail emails: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def send_email(self, to: Union[str, List[str]], subject: str, body: str, account_id: Optional[str] = None, 
                   body_type: str = "html", cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None) -> Dict[str, Any]:
        """Send Gmail email"""
        account_id = account_id or self.account_id
        if not account_id:
            return {
                "success": False,
                "error": "Account ID is required"
            }
        
        # Handle single email string or list of emails
        if isinstance(to, str):
            to = [to]
        
        payload = {
            "to": to,
            "subject": subject,
            "body": body,
            "body_type": body_type
        }
        
        if cc:
            payload["cc"] = cc
        if bcc:
            payload["bcc"] = bcc
        
        try:
            response = requests.post(f"{self.base_url}/gmail/accounts/{account_id}/emails/", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Gmail Send Email Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error sending Gmail email: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def get_email(self, email_id: str, account_id: Optional[str] = None, include_thread: bool = False, 
                  include_attachments: bool = True, mark_as_read: bool = False) -> Dict[str, Any]:
        """Get specific Gmail email"""
        account_id = account_id or self.account_id
        if not account_id:
            return {
                "success": False,
                "error": "Account ID is required"
            }
        
        params = {
            'include_thread': str(include_thread).lower(),
            'include_attachments': str(include_attachments).lower(),
            'mark_as_read': str(mark_as_read).lower()
        }
        
        try:
            response = requests.get(f"{self.base_url}/gmail/accounts/{account_id}/emails/{email_id}/", params=params)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Gmail Email Get Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting Gmail email: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def update_email(self, email_id: str, account_id: Optional[str] = None, is_read: Optional[bool] = None, 
                     is_starred: Optional[bool] = None) -> Dict[str, Any]:
        """Update Gmail email status"""
        account_id = account_id or self.account_id
        if not account_id:
            return {
                "success": False,
                "error": "Account ID is required"
            }
        
        payload = {}
        if is_read is not None:
            payload['is_read'] = is_read
        if is_starred is not None:
            payload['is_starred'] = is_starred
        
        if not payload:
            return {
                "success": False,
                "error": "At least one update parameter (is_read or is_starred) is required"
            }
        
        try:
            response = requests.put(f"{self.base_url}/gmail/accounts/{account_id}/emails/{email_id}/", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Gmail Email Update Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error updating Gmail email: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def delete_email(self, email_id: str, account_id: Optional[str] = None, permanent: bool = False) -> Dict[str, Any]:
        """Delete Gmail email"""
        account_id = account_id or self.account_id
        if not account_id:
            return {
                "success": False,
                "error": "Account ID is required"
            }
        
        params = {'permanent': str(permanent).lower()}
        
        try:
            response = requests.delete(f"{self.base_url}/gmail/accounts/{account_id}/emails/{email_id}/", params=params)
            response.raise_for_status()
            
            logger.info(f"Gmail Email Delete Response: {response.status_code}")
            return {
                "success": True,
                "status_code": response.status_code
            }
        except requests.RequestException as e:
            logger.error(f"Error deleting Gmail email: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    # Attachment Methods
    def get_attachment(self, email_id: str, attachment_id: str, account_id: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve Gmail email attachment"""
        account_id = account_id or self.account_id
        if not account_id:
            return {
                "success": False,
                "error": "Account ID is required"
            }
        
        try:
            response = requests.get(f"{self.base_url}/gmail/accounts/{account_id}/emails/{email_id}/attachments/{attachment_id}/")
            response.raise_for_status()
            
            logger.info(f"Gmail Attachment Response: {response.status_code} - Content length: {len(response.content)}")
            return {
                "success": True,
                "content": response.content,
                "headers": dict(response.headers),
                "content_length": len(response.content)
            }
        except requests.RequestException as e:
            logger.error(f"Error retrieving Gmail attachment: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    # Folder/Label Methods
    def list_folders(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """List Gmail folders/labels"""
        account_id = account_id or self.account_id
        if not account_id:
            return {
                "success": False,
                "error": "Account ID is required"
            }
        
        try:
            response = requests.get(f"{self.base_url}/gmail/accounts/{account_id}/folders/")
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Gmail Folders List Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error listing Gmail folders: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def get_folder_details(self, folder_id: str, account_id: Optional[str] = None) -> Dict[str, Any]:
        """Get Gmail folder details"""
        account_id = account_id or self.account_id
        if not account_id:
            return {
                "success": False,
                "error": "Account ID is required"
            }
        
        try:
            response = requests.get(f"{self.base_url}/gmail/accounts/{account_id}/folders/{folder_id}/")
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Gmail Folder Details Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting Gmail folder details: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    # Draft Methods
    def create_draft(self, to_email: str, subject: str, body: str, account_id: Optional[str] = None) -> Dict[str, Any]:
        """Create Gmail draft"""
        account_id = account_id or self.account_id
        if not account_id:
            return {
                "success": False,
                "error": "Account ID is required"
            }
        
        payload = {
            "to_email": to_email,
            "subject": subject,
            "body": body
        }
        
        try:
            response = requests.post(f"{self.base_url}/gmail/accounts/{account_id}/drafts/", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Gmail Create Draft Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error creating Gmail draft: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    # High-level convenience methods
    def complete_oauth_flow(self, client_id: Optional[str] = None, client_secret: Optional[str] = None, 
                           redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        """Complete OAuth flow and connect account"""
        # Get OAuth URL
        oauth_result = self.get_oauth_url()
        if not oauth_result["success"]:
            return oauth_result
        
        auth_url = oauth_result["auth_url"]
        
        return {
            "success": True,
            "message": "OAuth URL generated. Please complete authorization manually.",
            "auth_url": auth_url,
            "instructions": [
                "1. Visit the auth_url to authorize",
                "2. Copy the authorization code from the callback URL",
                "3. Use handle_oauth_callback_post() with the code",
                "4. Use connect_account() with the received tokens"
            ]
        }
    
    def mark_as_read(self, email_id: str, account_id: Optional[str] = None) -> Dict[str, Any]:
        """Mark email as read"""
        return self.update_email(email_id, account_id, is_read=True)
    
    def mark_as_unread(self, email_id: str, account_id: Optional[str] = None) -> Dict[str, Any]:
        """Mark email as unread"""
        return self.update_email(email_id, account_id, is_read=False)
    
    def star_email(self, email_id: str, account_id: Optional[str] = None) -> Dict[str, Any]:
        """Star email"""
        return self.update_email(email_id, account_id, is_starred=True)
    
    def unstar_email(self, email_id: str, account_id: Optional[str] = None) -> Dict[str, Any]:
        """Unstar email"""
        return self.update_email(email_id, account_id, is_starred=False)
    
    def get_unread_emails(self, account_id: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """Get unread emails"""
        return self.list_emails(account_id, limit=limit, unread_only=True)
    
    def get_inbox_emails(self, account_id: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """Get inbox emails"""
        return self.list_emails(account_id, limit=limit, folder='INBOX')


# Convenience function
def gmail_client(base_url: Optional[str] = None) -> GmailAPIClient:
    """Create a Gmail API client instance"""
    return GmailAPIClient(base_url)


# Interactive helper functions
def setup_gmail_oauth_interactive(client: GmailAPIClient) -> Dict[str, Any]:
    """Interactive OAuth setup for Gmail"""
    print("\n" + "="*80)
    print("GMAIL OAUTH SETUP")
    print("="*80)
    
    # Step 1: Get OAuth URL
    print("Step 1: Getting OAuth authorization URL...")
    oauth_result = client.get_oauth_url()
    
    if not oauth_result["success"]:
        return oauth_result
    
    auth_url = oauth_result["auth_url"]
    
    # Step 2: Display URL
    print(f"\nStep 2: Please visit this URL to authorize:")
    print(f"{auth_url}")
    print(f"\nAfter authorization, copy the authorization code from the callback URL")
    
    # Step 3: Get code from user
    auth_code = input("\nEnter the authorization code: ").strip()
    if not auth_code:
        return {
            "success": False,
            "error": "No authorization code provided"
        }
    
    # Step 4: Exchange code for tokens
    print("\nStep 3: Exchanging code for tokens...")
    callback_result = client.handle_oauth_callback_post(auth_code)
    
    if not callback_result["success"]:
        return callback_result
    
    access_token = callback_result["access_token"]
    refresh_token = callback_result["refresh_token"]
    
    # Step 5: Connect account
    print("\nStep 4: Connecting Gmail account...")
    connect_result = client.connect_account(access_token, refresh_token)
    
    if connect_result["success"]:
        print("\n" + "="*80)
        print("OAUTH FLOW COMPLETED SUCCESSFULLY")
        print("="*80)
        print(f"Account ID: {connect_result.get('account_id', 'N/A')}")
        print("="*80)
    
    return connect_result


def send_email_interactive(client: GmailAPIClient) -> Dict[str, Any]:
    """Interactive function to send email"""
    account_id = client.account_id or input("Enter Gmail account ID: ").strip()
    if not account_id:
        return {
            "success": False,
            "error": "Account ID is required"
        }
    
    to_email = input("Enter recipient email address: ").strip()
    if not to_email:
        return {
            "success": False,
            "error": "Recipient email is required"
        }
    
    subject = input("Enter email subject: ").strip()
    if not subject:
        subject = "Test Email from API"
    
    body = input("Enter email body: ").strip()
    if not body:
        body = "This is a test email sent via the Gmail API."
    
    return client.send_email(to_email, subject, body, account_id)


def manage_emails_interactive(client: GmailAPIClient) -> Dict[str, Any]:
    """Interactive function to manage emails"""
    account_id = client.account_id or input("Enter Gmail account ID: ").strip()
    if not account_id:
        return {
            "success": False,
            "error": "Account ID is required"
        }
    
    action = input("What do you want to do? (list/get/update/delete): ").strip().lower()
    
    if action == "list":
        limit = input("Enter limit (default 10): ").strip()
        limit = int(limit) if limit.isdigit() else 10
        
        folder = input("Enter folder (default INBOX): ").strip()
        folder = folder if folder else "INBOX"
        
        unread_only = input("Unread only? (y/n, default n): ").strip().lower()
        unread_only = unread_only == 'y'
        
        return client.list_emails(account_id, limit=limit, folder=folder, unread_only=unread_only)
    
    elif action == "get":
        email_id = input("Enter email ID: ").strip()
        if not email_id:
            return {
                "success": False,
                "error": "Email ID is required"
            }
        return client.get_email(email_id, account_id)
    
    elif action == "update":
        email_id = input("Enter email ID: ").strip()
        if not email_id:
            return {
                "success": False,
                "error": "Email ID is required"
            }
        
        is_read = input("Mark as read? (y/n/skip): ").strip().lower()
        is_starred = input("Mark as starred? (y/n/skip): ").strip().lower()
        
        is_read_val = None if is_read == 'skip' else (is_read == 'y')
        is_starred_val = None if is_starred == 'skip' else (is_starred == 'y')
        
        return client.update_email(email_id, account_id, is_read_val, is_starred_val)
    
    elif action == "delete":
        email_id = input("Enter email ID: ").strip()
        if not email_id:
            return {
                "success": False,
                "error": "Email ID is required"
            }
        
        permanent = input("Permanent delete? (y/n, default n): ").strip().lower()
        permanent = permanent == 'y'
        
        return client.delete_email(email_id, account_id, permanent)
    
    else:
        return {
            "success": False,
            "error": "Invalid action. Choose from: list, get, update, delete"
        }