import requests
import logging
import os
from typing import Optional, Dict, Any, List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhatsAppAPIClient:
    """WhatsApp API client for testing and interacting with WhatsApp endpoints"""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("API_URL", "")
        if not self.base_url:
            raise ValueError("API_URL must be provided either as parameter or environment variable")
    

    def get_auth_url(self) -> Dict[str, Any]:
        """Get WhatsApp authentication URL"""
        try:
            response = requests.get(f"{self.base_url}/whatsapp/auth/")
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Auth URL Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting auth URL: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
        
    def oauth_callback(self, code: str) -> Dict[str, Any]:
        """Handle OAuth callback with authorization code"""
        payload = {"code": code}
        
        try:
            response = requests.post(f"{self.base_url}/whatsapp/oauth/callback/", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"OAuth Callback Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error in OAuth callback: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
        finally:
            # Clean up any resources if needed
            pass

    # Flow and Webhook Management
    def create_flow(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new WhatsApp flow"""
        try:
            response = requests.post(f"{self.base_url}/whatsapp/create-flow/", json=flow_data)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Create Flow Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error creating flow: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def test_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test webhook endpoint"""
        try:
            response = requests.post(f"{self.base_url}/whatsapp/webhook/", json=webhook_data)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Webhook Test Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error testing webhook: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def send_batch_message(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send batch WhatsApp messages"""
        payload = {"messages": messages}
        
        try:
            response = requests.post(f"{self.base_url}/whatsapp/send-message/", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Batch Send Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error sending batch messages: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def query_gpt_test(self, query: str) -> Dict[str, Any]:
        """Test GPT query endpoint"""
        payload = {"query": query}
        
        try:
            response = requests.post(f"{self.base_url}/whatsapp/whapi/query-gpt-test/", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"GPT Query Test Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error testing GPT query: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    # Channel Management
    def get_channel_health(self) -> Dict[str, Any]:
        """Get WhatsApp channel health status"""
        try:
            response = requests.get(f"{self.base_url}/whatsapp/whapi/health/")
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Channel Health Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting channel health: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def get_channel_settings(self) -> Dict[str, Any]:
        """Get WhatsApp channel settings"""
        try:
            response = requests.get(f"{self.base_url}/whatsapp/whapi/settings/")
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Channel Settings Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting channel settings: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def get_channel_events(self) -> Dict[str, Any]:
        """Get WhatsApp channel events"""
        try:
            response = requests.get(f"{self.base_url}/whatsapp/whapi/settings/events/")
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Channel Events Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting channel events: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def get_channel_limits(self) -> Dict[str, Any]:
        """Get WhatsApp channel limits"""
        try:
            response = requests.get(f"{self.base_url}/whatsapp/whapi/limits/")
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Channel Limits Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting channel limits: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    # User Management
    def user_login(self, phone_number: Optional[str] = None) -> Dict[str, Any]:
        """Login WhatsApp user"""
        url = f"{self.base_url}/whatsapp/whapi/users/login/"
        if phone_number:
            url += f"{phone_number}/"
        
        try:
            response = requests.post(url)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"User Login Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error in user login: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def user_logout(self) -> Dict[str, Any]:
        """Logout WhatsApp user"""
        try:
            response = requests.post(f"{self.base_url}/whatsapp/whapi/users/logout/")
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"User Logout Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error in user logout: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Get WhatsApp user profile"""
        try:
            response = requests.get(f"{self.base_url}/whatsapp/whapi/users/profile/")
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"User Profile Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting user profile: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get WhatsApp user info"""
        try:
            response = requests.get(f"{self.base_url}/whatsapp/whapi/users/info/")
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"User Info Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting user info: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def get_user_status(self) -> Dict[str, Any]:
        """Get WhatsApp user status"""
        try:
            response = requests.get(f"{self.base_url}/whatsapp/whapi/status/")
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"User Status Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting user status: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    # Message Management
    def get_messages_list(self, chat_id: Optional[str] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get WhatsApp messages list"""
        url = f"{self.base_url}/whatsapp/whapi/messages/list/"
        if chat_id:
            url += f"{chat_id}/"
        
        params = {}
        if limit:
            params['limit'] = limit
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Messages List Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting messages list: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def send_text_message(self, to: str, text: str) -> Dict[str, Any]:
        """Send WhatsApp text message"""
        payload = {
            "to": to,
            "body": text
        }
        
        try:
            response = requests.post(f"{self.base_url}/whatsapp/whapi/messages/text/", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Send Text Message Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error sending text message: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def send_image_message(self, to: str, media_url: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """Send WhatsApp image message"""
        payload = {
            "to": to,
            "media": media_url,
            "caption": caption or ""
        }
        
        try:
            response = requests.post(f"{self.base_url}/whatsapp/whapi/messages/image/", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Send Image Message Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error sending image message: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def send_video_message(self, to: str, media_url: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """Send WhatsApp video message"""
        payload = {
            "to": to,
            "media": media_url,
            "caption": caption or ""
        }
        
        try:
            response = requests.post(f"{self.base_url}/whatsapp/whapi/messages/video/", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Send Video Message Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error sending video message: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def send_document_message(self, to: str, media_url: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """Send WhatsApp document message"""
        payload = {
            "to": to,
            "media": media_url,
            "filename": filename or "document.pdf"
        }
        
        try:
            response = requests.post(f"{self.base_url}/whatsapp/whapi/messages/document/", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Send Document Message Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error sending document message: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def send_location_message(self, to: str, latitude: str, longitude: str, name: Optional[str] = None, address: Optional[str] = None) -> Dict[str, Any]:
        """Send WhatsApp location message"""
        payload = {
            "to": to,
            "lat": latitude,
            "lng": longitude,
            "name": name or "",
            "address": address or ""
        }
        
        try:
            response = requests.post(f"{self.base_url}/whatsapp/whapi/messages/location/", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Send Location Message Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error sending location message: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def send_contact_message(self, to: str, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send WhatsApp contact message"""
        payload = {
            "to": to,
            **contact_data
        }
        
        try:
            response = requests.post(f"{self.base_url}/whatsapp/whapi/messages/contact/", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Send Contact Message Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error sending contact message: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def send_poll_message(self, to: str, name: str, options: List[str], count: int = 1) -> Dict[str, Any]:
        """Send WhatsApp poll message"""
        payload = {
            "to": to,
            "name": name,
            "options": options,
            "count": count
        }
        
        try:
            response = requests.post(f"{self.base_url}/whatsapp/whapi/messages/poll/", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Send Poll Message Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error sending poll message: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    # Chat and Contact Management
    def get_chats(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get WhatsApp chats list"""
        params = {}
        if limit:
            params['limit'] = limit
        
        try:
            response = requests.get(f"{self.base_url}/whatsapp/whapi/chats/", params=params)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Chats List Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting chats: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def get_chat_detail(self, chat_id: str) -> Dict[str, Any]:
        """Get WhatsApp chat details"""
        try:
            response = requests.get(f"{self.base_url}/whatsapp/whapi/chats/{chat_id}/")
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Chat Detail Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting chat detail: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def get_contacts(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get WhatsApp contacts list"""
        params = {}
        if limit:
            params['limit'] = limit
        
        try:
            response = requests.get(f"{self.base_url}/whatsapp/whapi/contacts/", params=params)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Contacts List Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting contacts: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def get_contact_detail(self, contact_id: str) -> Dict[str, Any]:
        """Get WhatsApp contact details"""
        try:
            response = requests.get(f"{self.base_url}/whatsapp/whapi/contacts/{contact_id}/")
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Contact Detail Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting contact detail: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    # Group Management
    def get_groups(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get WhatsApp groups list"""
        params = {}
        if limit:
            params['limit'] = limit
        
        try:
            response = requests.get(f"{self.base_url}/whatsapp/whapi/groups/", params=params)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Groups List Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting groups: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def get_group_detail(self, group_id: str) -> Dict[str, Any]:
        """Get WhatsApp group details"""
        try:
            response = requests.get(f"{self.base_url}/whatsapp/whapi/groups/{group_id}/")
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Group Detail Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting group detail: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    # Business Features
    def get_business_info(self) -> Dict[str, Any]:
        """Get WhatsApp business information"""
        try:
            response = requests.get(f"{self.base_url}/whatsapp/whapi/business/")
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Business Info Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting business info: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def get_business_products(self, contact_id: Optional[str] = None) -> Dict[str, Any]:
        """Get WhatsApp business products"""
        url = f"{self.base_url}/whatsapp/whapi/business/"
        if contact_id:
            url += f"{contact_id}/"
        url += "products/"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Business Products Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting business products: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    # Media Management
    def upload_media(self, media_url: str) -> Dict[str, Any]:
        """Upload media to WhatsApp"""
        payload = {"media": media_url}
        
        try:
            response = requests.post(f"{self.base_url}/whatsapp/whapi/media/", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Media Upload Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error uploading media: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    def get_media_detail(self, media_id: str) -> Dict[str, Any]:
        """Get media details"""
        try:
            response = requests.get(f"{self.base_url}/whatsapp/whapi/media/{media_id}/")
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Media Detail Response: {result}")
            return {
                "success": True,
                "data": result
            }
        except requests.RequestException as e:
            logger.error(f"Error getting media detail: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }


# Convenience functions for easy usage
def whatsapp_client(base_url: Optional[str] = None) -> WhatsAppAPIClient:
    """Create a WhatsApp API client instance"""
    return WhatsAppAPIClient(base_url)


# Interactive helper functions
def send_text_message_interactive(client: WhatsAppAPIClient) -> Dict[str, Any]:
    """Interactive function to send text message"""
    to_number = input("Enter recipient phone number: ").strip()
    message_text = input("Enter message text: ").strip()
    
    if not to_number or not message_text:
        return {
            "success": False,
            "error": "Phone number and message text are required"
        }
    
    return client.send_text_message(to_number, message_text)


def send_media_message_interactive(client: WhatsAppAPIClient) -> Dict[str, Any]:
    """Interactive function to send media message"""
    to_number = input("Enter recipient phone number: ").strip()
    media_type = input("Enter media type (image/video/document): ").strip().lower()
    media_url = input("Enter media URL: ").strip()
    caption = input("Enter caption (optional): ").strip()
    
    if not to_number or not media_url:
        return {
            "success": False,
            "error": "Phone number and media URL are required"
        }
    
    if media_type == "image":
        return client.send_image_message(to_number, media_url, caption)
    elif media_type == "video":
        return client.send_video_message(to_number, media_url, caption)
    elif media_type == "document":
        filename = input("Enter filename (optional): ").strip()
        return client.send_document_message(to_number, media_url, filename)
    else:
        return {
            "success": False,
            "error": "Invalid media type. Choose from: image, video, document"
        }


def get_whatsapp_data_interactive(client: WhatsAppAPIClient) -> Dict[str, Any]:
    """Interactive function to get various WhatsApp data"""
    data_type = input("What data do you want to retrieve? (chats/contacts/groups/messages): ").strip().lower()
    
    results = {}
    
    if data_type == "chats":
        results["chats"] = client.get_chats(limit=10)
    elif data_type == "contacts":
        results["contacts"] = client.get_contacts(limit=10)
    elif data_type == "groups":
        results["groups"] = client.get_groups(limit=10)
    elif data_type == "messages":
        chat_id = input("Enter chat ID (optional): ").strip()
        results["messages"] = client.get_messages_list(chat_id, limit=10)
    else:
        return {
            "success": False,
            "error": "Invalid data type. Choose from: chats, contacts, groups, messages"
        }
    
    return results