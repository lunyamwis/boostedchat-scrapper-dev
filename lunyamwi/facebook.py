import requests
import logging
import os
from typing import Optional, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FacebookAPIClient:
    """Facebook API client for testing and interacting with Facebook endpoints"""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("API_URL", "")
        if not self.base_url:
            raise ValueError("API_URL must be provided either as parameter or environment variable")
    
    def get_auth_url(self) -> Dict[str, Any]:
        """Get Facebook authentication URL"""
        try:
            response = requests.get(f"{self.base_url}/facebook/auth/")
            response.raise_for_status()
            
            result = response.json()
            auth_url = result.get('auth_url')
            if auth_url:
                print(f"Visit this URL to authenticate: {auth_url}")
            
            logger.info(f"Facebook Auth URL Response: {result}")
            return {
                "success": True,
                "data": result,
                "auth_url": auth_url
            }
        except requests.RequestException as e:
            logger.error(f"Error getting auth URL: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def handle_auth_callback(self, auth_code: str) -> Dict[str, Any]:
        """Handle Facebook authentication callback"""
        if not auth_code:
            return {
                "success": False,
                "error": "No auth code provided"
            }
        
        try:
            response = requests.get(f"{self.base_url}/facebook/auth/callback/", params={"code": auth_code})
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Facebook Auth Callback Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error in auth callback: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def get_messenger_profile(self) -> Dict[str, Any]:
        """Get Facebook messenger profile"""
        try:
            response = requests.get(f"{self.base_url}/facebook/messenger-profile/")
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Facebook Messenger Profile Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting messenger profile: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def get_user_me(self) -> Dict[str, Any]:
        """Get current Facebook user information"""
        try:
            response = requests.get(f"{self.base_url}/facebook/users/me/")
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Facebook User Me Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting user me: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def send_message(self, recipient_id: str, message_text: str) -> Dict[str, Any]:
        """Send Facebook message"""
        if not recipient_id:
            return {
                "success": False,
                "error": "No recipient ID provided"
            }
        
        if not message_text:
            message_text = "Test message from API"
        
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
        
        try:
            response = requests.post(f"{self.base_url}/facebook/messages/", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Facebook Send Message Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error sending message: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def send_batch_request(self, batch_requests: Optional[list] = None) -> Dict[str, Any]:
        """Send Facebook batch request"""
        if not batch_requests:
            batch_requests = [
                {
                    "method": "GET",
                    "relative_url": "me"
                },
                {
                    "method": "GET", 
                    "relative_url": "me/accounts"
                }
            ]
        
        payload = {"batch": batch_requests}
        
        try:
            response = requests.post(f"{self.base_url}/facebook/batch/", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Facebook Batch Request Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error in batch request: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def get_page_posts(self, page_id: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get Facebook page posts"""
        if not page_id:
            return {
                "success": False,
                "error": "No page ID provided"
            }
        
        params = {}
        if limit:
            params['limit'] = limit
        
        try:
            response = requests.get(f"{self.base_url}/facebook/pages/{page_id}/posts/", params=params)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Facebook Page Posts Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting page posts: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def get_page_insights(self, page_id: str, metrics: Optional[list] = None) -> Dict[str, Any]:
        """Get Facebook page insights"""
        if not page_id:
            return {
                "success": False,
                "error": "No page ID provided"
            }
        
        params = {}
        if metrics:
            params['metrics'] = ','.join(metrics)
        
        try:
            response = requests.get(f"{self.base_url}/facebook/pages/{page_id}/insights/", params=params)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Facebook Page Insights Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting page insights: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def get_page_conversations(self, page_id: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get Facebook page conversations"""
        if not page_id:
            return {
                "success": False,
                "error": "No page ID provided"
            }
        
        params = {}
        if limit:
            params['limit'] = limit
        
        try:
            response = requests.get(f"{self.base_url}/facebook/pages/{page_id}/conversations/", params=params)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Facebook Page Conversations Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting page conversations: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def create_post(self, page_id: str, message: str, **kwargs) -> Dict[str, Any]:
        """Create Facebook post"""
        if not page_id:
            return {
                "success": False,
                "error": "No page ID provided"
            }
        
        if not message:
            message = "Test post from API"
        
        payload = {"message": message}
        payload.update(kwargs)  # Allow additional parameters like link, photo, etc.
        
        try:
            response = requests.post(f"{self.base_url}/facebook/pages/{page_id}/posts/", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Facebook Create Post Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error creating post: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def get_page_photos(self, page_id: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get Facebook page photos"""
        if not page_id:
            return {
                "success": False,
                "error": "No page ID provided"
            }
        
        params = {}
        if limit:
            params['limit'] = limit
        
        try:
            response = requests.get(f"{self.base_url}/facebook/pages/{page_id}/photos/", params=params)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Facebook Page Photos Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting page photos: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }


# Convenience functions for easy usage
def facebook_client(base_url: Optional[str] = None) -> FacebookAPIClient:
    """Create a Facebook API client instance"""
    return FacebookAPIClient(base_url)


# Example usage functions
def facebook_auth_flow(client: FacebookAPIClient) -> Dict[str, Any]:
    """Complete Facebook authentication flow"""
    # Step 1: Get auth URL
    auth_result = client.get_auth_url()
    if not auth_result["success"]:
        return auth_result
    
    # Step 2: Get auth code from user
    auth_code = input("Enter the Facebook auth code from the URL after login: ").strip()
    if not auth_code:
        return {
            "success": False,
            "error": "No auth code provided"
        }
    
    # Step 3: Handle callback
    return client.handle_auth_callback(auth_code)


def send_facebook_message_interactive(client: FacebookAPIClient) -> Dict[str, Any]:
    """Interactive function to send Facebook message"""
    recipient_id = input("Enter recipient ID: ").strip()
    message_text = input("Enter message text: ").strip()
    
    return client.send_message(recipient_id, message_text)


def create_facebook_post_interactive(client: FacebookAPIClient) -> Dict[str, Any]:
    """Interactive function to create Facebook post"""
    page_id = input("Enter Facebook page ID for posting: ").strip()
    message = input("Enter post message: ").strip()
    
    return client.create_post(page_id, message)


def get_page_data_interactive(client: FacebookAPIClient) -> Dict[str, Any]:
    """Interactive function to get page data (posts, insights, photos)"""
    page_id = input("Enter Facebook page ID: ").strip()
    
    results = {}
    
    # Get posts
    results["posts"] = client.get_page_posts(page_id, limit=10)
    
    # Get insights
    results["insights"] = client.get_page_insights(page_id)
    
    # Get photos
    results["photos"] = client.get_page_photos(page_id, limit=10)
    
    # Get conversations
    results["conversations"] = client.get_page_conversations(page_id, limit=10)
    
    return results