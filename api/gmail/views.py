from django.shortcuts import render
import json
import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from dotenv import load_dotenv
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

load_dotenv()

# Unipile Configuration
LUNYAMWI_GMAIL_BASE_URL = os.getenv("LUNYAMWI_LINKEDIN_BASE_URL", "htps://example.com")
LUNYAMWI_GMAIL_API_KEY = os.getenv("LUNYAMWI_GMAIL_API_KEY", "your_lunyamwi_gmail_api_key_here")

# Headers for Unipile API requests
LUNYAMWI_GMAIL_HEADERS = {
    "X-API-KEY": LUNYAMWI_GMAIL_API_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def make_lunyamwi_gmail_request(method: str, endpoint: str, params: Dict = None, data: Dict = None, headers: Dict = None) -> Dict:
    """Helper function to make requests to Unipile API"""
    url = f"{LUNYAMWI_GMAIL_BASE_URL}{endpoint}"
    
    request_headers = LUNYAMWI_GMAIL_HEADERS.copy()
    if headers:
        request_headers.update(headers)
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=request_headers, params=params)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=request_headers, params=params, json=data)
        elif method.upper() == 'PUT':
            response = requests.put(url, headers=request_headers, params=params, json=data)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=request_headers, params=params)
        elif method.upper() == 'PATCH':
            response = requests.patch(url, headers=request_headers, params=params, json=data)
        else:
            return {"success": False, "error": "Unsupported HTTP method", "status_code": 400}
        
        return {
            "success": response.ok,
            "data": response.json() if response.content else {},
            "status_code": response.status_code,
            "headers": dict(response.headers)
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": getattr(e.response, 'status_code', 500) if hasattr(e, 'response') else 500
        }
    except Exception as e:
        return {"success": False, "error": str(e), "status_code": 500}

def handle_lunyamwi_gmail_error(func):
    """Decorator to handle Unipile API errors"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return Response({
                "error": f"An error occurred: {str(e)}",
                "error_code": "internal_error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return wrapper


class GmailAccountsView(APIView):
    """Gmail Accounts management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request):
        """Get all Gmail accounts"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'provider': 'gmail'
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_gmail_request("GET", "/accounts", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def post(self, request):
        """Add Gmail account"""
        payload = {
            "provider": "gmail",
            "name": request.data.get("name"),
            "email": request.data.get("email"),
            "password": request.data.get("password"),
            "app_password": request.data.get("app_password"),  # For 2FA accounts
            "oauth_token": request.data.get("oauth_token"),
            "oauth_refresh_token": request.data.get("oauth_refresh_token"),
            "settings": request.data.get("settings", {})
        }
        
        result = make_lunyamwi_gmail_request("POST", "/accounts", data=payload)
        return Response(result, status=result.get('status_code', 500))

class GmailAccountView(APIView):
    """Single Gmail Account management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id):
        """Get Gmail account details"""
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def put(self, request, account_id):
        """Update Gmail account"""
        result = make_lunyamwi_gmail_request("PUT", f"/accounts/{account_id}", data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def delete(self, request, account_id):
        """Delete Gmail account"""
        result = make_lunyamwi_gmail_request("DELETE", f"/accounts/{account_id}")
        return Response(result, status=result.get('status_code', 500))

class GmailAccountConnectView(APIView):
    """Connect Gmail account"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id):
        """Connect to Gmail account"""
        payload = {
            "oauth_code": request.data.get("oauth_code"),
            "redirect_uri": request.data.get("redirect_uri")
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/connect", data=payload)
        return Response(result, status=result.get('status_code', 500))

class GmailAccountDisconnectView(APIView):
    """Disconnect Gmail account"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id):
        """Disconnect Gmail account"""
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/disconnect")
        return Response(result, status=result.get('status_code', 500))


class GmailEmailsView(APIView):
    """Gmail Emails management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id):
        """Get emails from Gmail"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'folder': request.query_params.get('folder', 'INBOX'),  # INBOX, SENT, DRAFTS, TRASH, SPAM
            'unread_only': request.query_params.get('unread_only', 'false'),
            'from': request.query_params.get('from'),
            'to': request.query_params.get('to'),
            'subject': request.query_params.get('subject'),
            'body_contains': request.query_params.get('body_contains'),
            'has_attachment': request.query_params.get('has_attachment'),
            'since': request.query_params.get('since'),
            'until': request.query_params.get('until'),
            'label': request.query_params.get('label'),
            'category': request.query_params.get('category'),  # primary, social, promotions, updates, forums
            'importance': request.query_params.get('importance'),  # high, normal, low
            'thread_id': request.query_params.get('thread_id')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/emails", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id):
        """Send email via Gmail"""
        payload = {
            "to": request.data.get("to"),
            "cc": request.data.get("cc", []),
            "bcc": request.data.get("bcc", []),
            "subject": request.data.get("subject"),
            "body": request.data.get("body"),
            "body_type": request.data.get("body_type", "html"),  # html, plain
            "attachments": request.data.get("attachments", []),
            "reply_to": request.data.get("reply_to"),
            "in_reply_to": request.data.get("in_reply_to"),  # Message ID for replies
            "references": request.data.get("references"),  # For threading
            "scheduled_at": request.data.get("scheduled_at"),  # ISO datetime string
            "send_later": request.data.get("send_later", False),
            "tracking": request.data.get("tracking", {
                "opens": True,
                "clicks": True,
                "replies": True
            }),
            "template_id": request.data.get("template_id"),
            "variables": request.data.get("variables", {}),  # For template variables
            "priority": request.data.get("priority", "normal"),  # high, normal, low
            "read_receipt": request.data.get("read_receipt", False),
            "delivery_receipt": request.data.get("delivery_receipt", False)
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/emails", data=payload)
        return Response(result, status=result.get('status_code', 500))

class GmailEmailView(APIView):
    """Single Gmail Email management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id, email_id):
        """Get specific email"""
        params = {
            'include_thread': request.query_params.get('include_thread', 'false'),
            'include_attachments': request.query_params.get('include_attachments', 'true'),
            'mark_as_read': request.query_params.get('mark_as_read', 'false')
        }
        
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/emails/{email_id}", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def put(self, request, account_id, email_id):
        """Update email (mark as read/unread, add labels, etc.)"""
        payload = {
            "is_read": request.data.get("is_read"),
            "is_starred": request.data.get("is_starred"),
            "is_important": request.data.get("is_important"),
            "labels": request.data.get("labels"),  # Add/remove labels
            "folder": request.data.get("folder"),  # Move to folder
            "category": request.data.get("category")
        }
        
        result = make_lunyamwi_gmail_request("PUT", f"/accounts/{account_id}/emails/{email_id}", data=payload)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def delete(self, request, account_id, email_id):
        """Delete email (move to trash or permanent delete)"""
        params = {
            'permanent': request.query_params.get('permanent', 'false')
        }
        
        result = make_lunyamwi_gmail_request("DELETE", f"/accounts/{account_id}/emails/{email_id}", params=params)
        return Response(result, status=result.get('status_code', 500))

class GmailEmailReplyView(APIView):
    """Reply to Gmail emails"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id, email_id):
        """Reply to email"""
        payload = {
            "body": request.data.get("body"),
            "body_type": request.data.get("body_type", "html"),
            "reply_all": request.data.get("reply_all", False),
            "attachments": request.data.get("attachments", []),
            "scheduled_at": request.data.get("scheduled_at"),
            "tracking": request.data.get("tracking", {
                "opens": True,
                "clicks": True,
                "replies": True
            })
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/emails/{email_id}/reply", data=payload)
        return Response(result, status=result.get('status_code', 500))

class GmailEmailForwardView(APIView):
    """Forward Gmail emails"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id, email_id):
        """Forward email"""
        payload = {
            "to": request.data.get("to"),
            "cc": request.data.get("cc", []),
            "bcc": request.data.get("bcc", []),
            "body": request.data.get("body", ""),  # Additional message
            "include_attachments": request.data.get("include_attachments", True),
            "scheduled_at": request.data.get("scheduled_at"),
            "tracking": request.data.get("tracking", {
                "opens": True,
                "clicks": True
            })
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/emails/{email_id}/forward", data=payload)
        return Response(result, status=result.get('status_code', 500))


class GmailCampaignsView(APIView):
    """Email Campaigns management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id):
        """Get all campaigns"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'status': request.query_params.get('status'),  # draft, active, paused, completed
            'type': request.query_params.get('type')  # outreach, follow_up, drip, newsletter
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/campaigns", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id):
        """Create email campaign"""
        payload = {
            "name": request.data.get("name"),
            "type": request.data.get("type", "outreach"),  # outreach, follow_up, drip, newsletter
            "subject": request.data.get("subject"),
            "body": request.data.get("body"),
            "body_type": request.data.get("body_type", "html"),
            "recipients": request.data.get("recipients", []),  # List of email addresses
            "recipient_lists": request.data.get("recipient_lists", []),  # List IDs
            "schedule": request.data.get("schedule", {
                "start_date": None,
                "send_time": "09:00",
                "timezone": "UTC",
                "days_of_week": [1, 2, 3, 4, 5],  # Monday to Friday
                "frequency": "immediate"  # immediate, daily, weekly, monthly
            }),
            "settings": request.data.get("settings", {
                "track_opens": True,
                "track_clicks": True,
                "track_replies": True,
                "unsubscribe_link": True,
                "delay_between_emails": 60,  # seconds
                "max_emails_per_day": 50,
                "stop_on_reply": True,
                "personalization": True
            }),
            "templates": request.data.get("templates", []),  # Follow-up templates
            "attachments": request.data.get("attachments", []),
            "sender_name": request.data.get("sender_name"),
            "reply_to": request.data.get("reply_to")
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/campaigns", data=payload)
        return Response(result, status=result.get('status_code', 500))

class GmailCampaignView(APIView):
    """Single Email Campaign management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id, campaign_id):
        """Get campaign details"""
        params = {
            'include_analytics': request.query_params.get('include_analytics', 'true'),
            'include_recipients': request.query_params.get('include_recipients', 'false')
        }
        
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/campaigns/{campaign_id}", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def put(self, request, account_id, campaign_id):
        """Update campaign"""
        result = make_lunyamwi_gmail_request("PUT", f"/accounts/{account_id}/campaigns/{campaign_id}", data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def delete(self, request, account_id, campaign_id):
        """Delete campaign"""
        result = make_lunyamwi_gmail_request("DELETE", f"/accounts/{account_id}/campaigns/{campaign_id}")
        return Response(result, status=result.get('status_code', 500))

class GmailCampaignControlView(APIView):
    """Campaign control (start, pause, stop)"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id, campaign_id):
        """Control campaign (start/pause/stop)"""
        payload = {
            "action": request.data.get("action")  # start, pause, stop, resume
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/campaigns/{campaign_id}/control", data=payload)
        return Response(result, status=result.get('status_code', 500))

class GmailCampaignRecipientsView(APIView):
    """Campaign recipients management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id, campaign_id):
        """Get campaign recipients"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'status': request.query_params.get('status')  # pending, sent, opened, clicked, replied, bounced
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/campaigns/{campaign_id}/recipients", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id, campaign_id):
        """Add recipients to campaign"""
        payload = {
            "recipients": request.data.get("recipients", []),
            "recipient_lists": request.data.get("recipient_lists", [])
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/campaigns/{campaign_id}/recipients", data=payload)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def delete(self, request, account_id, campaign_id):
        """Remove recipients from campaign"""
        payload = {
            "recipient_ids": request.data.get("recipient_ids", [])
        }
        
        result = make_lunyamwi_gmail_request("DELETE", f"/accounts/{account_id}/campaigns/{campaign_id}/recipients", data=payload)
        return Response(result, status=result.get('status_code', 500))


class GmailSequencesView(APIView):
    """Email Sequences/Drip Campaigns"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id):
        """Get all email sequences"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'status': request.query_params.get('status')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/sequences", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id):
        """Create email sequence"""
        payload = {
            "name": request.data.get("name"),
            "description": request.data.get("description"),
            "steps": request.data.get("steps", []),  # List of sequence steps
            "trigger": request.data.get("trigger", {
                "type": "manual",  # manual, date, behavior, api
                "conditions": {}
            }),
            "settings": request.data.get("settings", {
                "track_opens": True,
                "track_clicks": True,
                "stop_on_reply": True,
                "working_days_only": True,
                "timezone": "UTC"
            })
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/sequences", data=payload)
        return Response(result, status=result.get('status_code', 500))

class GmailSequenceView(APIView):
    """Single Email Sequence management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id, sequence_id):
        """Get sequence details"""
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/sequences/{sequence_id}")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def put(self, request, account_id, sequence_id):
        """Update sequence"""
        result = make_lunyamwi_gmail_request("PUT", f"/accounts/{account_id}/sequences/{sequence_id}", data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def delete(self, request, account_id, sequence_id):
        """Delete sequence"""
        result = make_lunyamwi_gmail_request("DELETE", f"/accounts/{account_id}/sequences/{sequence_id}")
        return Response(result, status=result.get('status_code', 500))

class GmailSequenceEnrollView(APIView):
    """Enroll contacts in sequences"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id, sequence_id):
        """Enroll contacts in sequence"""
        payload = {
            "contacts": request.data.get("contacts", []),
            "start_step": request.data.get("start_step", 1),
            "variables": request.data.get("variables", {})
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/sequences/{sequence_id}/enroll", data=payload)
        return Response(result, status=result.get('status_code', 500))

class GmailTemplatesView(APIView):
    """Email Templates management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id):
        """Get all email templates"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'category': request.query_params.get('category'),  # outreach, follow_up, thank_you, etc.
            'search': request.query_params.get('search')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/templates", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id):
        """Create email template"""
        payload = {
            "name": request.data.get("name"),
            "subject": request.data.get("subject"),
            "body": request.data.get("body"),
            "body_type": request.data.get("body_type", "html"),
            "category": request.data.get("category"),
            "variables": request.data.get("variables", []),  # Template variables
            "attachments": request.data.get("attachments", []),
            "tags": request.data.get("tags", []),
            "is_shared": request.data.get("is_shared", False)
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/templates", data=payload)
        return Response(result, status=result.get('status_code', 500))

class GmailTemplateView(APIView):
    """Single Email Template management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id, template_id):
        """Get template details"""
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/templates/{template_id}")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def put(self, request, account_id, template_id):
        """Update template"""
        result = make_lunyamwi_gmail_request("PUT", f"/accounts/{account_id}/templates/{template_id}", data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def delete(self, request, account_id, template_id):
        """Delete template"""
        result = make_lunyamwi_gmail_request("DELETE", f"/accounts/{account_id}/templates/{template_id}")
        return Response(result, status=result.get('status_code', 500))

class GmailTemplatePreviewView(APIView):
    """Preview email template with variables"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id, template_id):
        """Preview template with sample data"""
        payload = {
            "variables": request.data.get("variables", {}),
            "contact_data": request.data.get("contact_data", {})
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/templates/{template_id}/preview", data=payload)
        return Response(result, status=result.get('status_code', 500))


class GmailContactListsView(APIView):
    """Contact Lists management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id):
        """Get all contact lists"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'search': request.query_params.get('search')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/contact-lists", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id):
        """Create contact list"""
        payload = {
            "name": request.data.get("name"),
            "description": request.data.get("description"),
            "tags": request.data.get("tags", []),
            "is_suppression_list": request.data.get("is_suppression_list", False)
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/contact-lists", data=payload)
        return Response(result, status=result.get('status_code', 500))

class GmailContactListView(APIView):
    """Single Contact List management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id, list_id):
        """Get contact list details"""
        params = {
            'include_contacts': request.query_params.get('include_contacts', 'false'),
            'limit': request.query_params.get('limit', 50)
        }
        
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/contact-lists/{list_id}", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def put(self, request, account_id, list_id):
        """Update contact list"""
        result = make_lunyamwi_gmail_request("PUT", f"/accounts/{account_id}/contact-lists/{list_id}", data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def delete(self, request, account_id, list_id):
        """Delete contact list"""
        result = make_lunyamwi_gmail_request("DELETE", f"/accounts/{account_id}/contact-lists/{list_id}")
        return Response(result, status=result.get('status_code', 500))

class GmailContactListContactsView(APIView):
    """Contact List contacts management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id, list_id):
        """Get contacts in list"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'search': request.query_params.get('search')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/contact-lists/{list_id}/contacts", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id, list_id):
        """Add contacts to list"""
        payload = {
            "contacts": request.data.get("contacts", []),
            "contact_ids": request.data.get("contact_ids", []),
            "csv_data": request.data.get("csv_data"),  # CSV import
            "deduplicate": request.data.get("deduplicate", True)
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/contact-lists/{list_id}/contacts", data=payload)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def delete(self, request, account_id, list_id):
        """Remove contacts from list"""
        payload = {
            "contact_ids": request.data.get("contact_ids", [])
        }
        
        result = make_lunyamwi_gmail_request("DELETE", f"/accounts/{account_id}/contact-lists/{list_id}/contacts", data=payload)
        return Response(result, status=result.get('status_code', 500))

class GmailContactsView(APIView):
    """Contacts management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id):
        """Get all contacts"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'search': request.query_params.get('search'),
            'list_id': request.query_params.get('list_id'),
            'tags': request.query_params.get('tags'),
            'status': request.query_params.get('status')  # active, bounced, unsubscribed, complained
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/contacts", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id):
        """Create contact"""
        payload = {
            "email": request.data.get("email"),
            "first_name": request.data.get("first_name"),
            "last_name": request.data.get("last_name"),
            "company": request.data.get("company"),
            "title": request.data.get("title"),
            "phone": request.data.get("phone"),
            "website": request.data.get("website"),
            "custom_fields": request.data.get("custom_fields", {}),
            "tags": request.data.get("tags", []),
            "lists": request.data.get("lists", []),  # List IDs to add contact to
            "notes": request.data.get("notes")
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/contacts", data=payload)
        return Response(result, status=result.get('status_code', 500))

class GmailContactView(APIView):
    """Single Contact management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id, contact_id):
        """Get contact details"""
        params = {
            'include_activity': request.query_params.get('include_activity', 'true'),
            'include_campaigns': request.query_params.get('include_campaigns', 'false')
        }
        
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/contacts/{contact_id}", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def put(self, request, account_id, contact_id):
        """Update contact"""
        result = make_lunyamwi_gmail_request("PUT", f"/accounts/{account_id}/contacts/{contact_id}", data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def delete(self, request, account_id, contact_id):
        """Delete contact"""
        result = make_lunyamwi_gmail_request("DELETE", f"/accounts/{account_id}/contacts/{contact_id}")
        return Response(result, status=result.get('status_code', 500))


class GmailTrackingView(APIView):
    """Email Tracking"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id):
        """Get email tracking data"""
        params = {
            'email_id': request.query_params.get('email_id'),
            'campaign_id': request.query_params.get('campaign_id'),
            'event_type': request.query_params.get('event_type'),  # open, click, reply, bounce
            'since': request.query_params.get('since'),
            'until': request.query_params.get('until'),
            'limit': request.query_params.get('limit', 50)
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/tracking", params=params)
        return Response(result, status=result.get('status_code', 500))

class GmailTrackingPixelView(APIView):
    """Email tracking pixel endpoint"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, tracking_id):
        """Handle tracking pixel requests"""
        # This would typically be a transparent 1x1 pixel
        params = {
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'ip_address': request.META.get('REMOTE_ADDR'),
            'timestamp': datetime.now().isoformat()
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/tracking/pixel/{tracking_id}", data=params)
        
        # Return a transparent pixel image
        from django.http import HttpResponse
        import base64
        
        # 1x1 transparent PNG
        pixel_data = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
        )
        
        response = HttpResponse(pixel_data, content_type='image/png')
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response

class GmailAnalyticsView(APIView):
    """Gmail Analytics"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id):
        """Get email analytics"""
        params = {
            'start_date': request.query_params.get('start_date'),
            'end_date': request.query_params.get('end_date'),
            'campaign_id': request.query_params.get('campaign_id'),
            'metrics': request.query_params.get('metrics'),  # sent, delivered, opened, clicked, replied, bounced
            'granularity': request.query_params.get('granularity', 'day'),  # hour, day, week, month
            'group_by': request.query_params.get('group_by')  # campaign, template, contact_list
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/analytics", params=params)
        return Response(result, status=result.get('status_code', 500))

class GmailCampaignAnalyticsView(APIView):
    """Campaign-specific analytics"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id, campaign_id):
        """Get campaign analytics"""
        params = {
            'include_recipients': request.query_params.get('include_recipients', 'false'),
            'breakdown_by': request.query_params.get('breakdown_by')  # day, recipient, template
        }
        
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/campaigns/{campaign_id}/analytics", params=params)
        return Response(result, status=result.get('status_code', 500))


class GmailDeliverabilityView(APIView):
    """Email Deliverability monitoring"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id):
        """Get deliverability metrics"""
        params = {
            'start_date': request.query_params.get('start_date'),
            'end_date': request.query_params.get('end_date')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/deliverability", params=params)
        return Response(result, status=result.get('status_code', 500))

class GmailDomainReputationView(APIView):
    """Domain reputation monitoring"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id):
        """Get domain reputation"""
        params = {
            'domain': request.query_params.get('domain')
        }
        
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/domain-reputation", params=params)
        return Response(result, status=result.get('status_code', 500))

class GmailSpamTestView(APIView):
    """Spam testing"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id):
        """Test email for spam score"""
        payload = {
            "subject": request.data.get("subject"),
            "body": request.data.get("body"),
            "from_email": request.data.get("from_email"),
            "attachments": request.data.get("attachments", [])
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/spam-test", data=payload)
        return Response(result, status=result.get('status_code', 500))

class GmailWarmupView(APIView):
    """Email warmup management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id):
        """Get warmup status"""
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/warmup")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id):
        """Start email warmup"""
        payload = {
            "warmup_type": request.data.get("warmup_type", "gradual"),  # gradual, aggressive, custom
            "daily_volume": request.data.get("daily_volume"),
            "duration_days": request.data.get("duration_days", 30),
            "settings": request.data.get("settings", {
                "reply_rate": 0.3,
                "mark_as_important_rate": 0.1,
                "move_to_primary_rate": 0.2
            })
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/warmup/start", data=payload)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def delete(self, request, account_id):
        """Stop email warmup"""
        result = make_lunyamwi_gmail_request("DELETE", f"/accounts/{account_id}/warmup/stop")
        return Response(result, status=result.get('status_code', 500))


class GmailAttachmentsView(APIView):
    """Email attachments management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id):
        """Upload attachment"""
        payload = {
            "file_name": request.data.get("file_name"),
            "file_data": request.data.get("file_data"),  # Base64 encoded
            "file_url": request.data.get("file_url"),
            "content_type": request.data.get("content_type")
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/attachments", data=payload)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id, attachment_id):
        """Get attachment"""
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/attachments/{attachment_id}")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def delete(self, request, account_id, attachment_id):
        """Delete attachment"""
        result = make_lunyamwi_gmail_request("DELETE", f"/accounts/{account_id}/attachments/{attachment_id}")
        return Response(result, status=result.get('status_code', 500))

class GmailFoldersView(APIView):
    """Gmail folders/labels management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id):
        """Get all folders/labels"""
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/folders")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id):
        """Create folder/label"""
        payload = {
            "name": request.data.get("name"),
            "color": request.data.get("color"),
            "type": request.data.get("type", "user")  # system, user
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/folders", data=payload)
        return Response(result, status=result.get('status_code', 500))

class GmailFolderView(APIView):
    """Single folder/label management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id, folder_id):
        """Get folder details"""
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/folders/{folder_id}")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def put(self, request, account_id, folder_id):
        """Update folder"""
        result = make_lunyamwi_gmail_request("PUT", f"/accounts/{account_id}/folders/{folder_id}", data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def delete(self, request, account_id, folder_id):
        """Delete folder"""
        result = make_lunyamwi_gmail_request("DELETE", f"/accounts/{account_id}/folders/{folder_id}")
        return Response(result, status=result.get('status_code', 500))


class GmailBulkOperationsView(APIView):
    """Bulk operations on emails"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id):
        """Perform bulk operations"""
        payload = {
            "operation": request.data.get("operation"),  # mark_read, mark_unread, delete, move, add_label, remove_label
            "email_ids": request.data.get("email_ids", []),
            "filters": request.data.get("filters", {}),  # Apply to emails matching filters
            "target_folder": request.data.get("target_folder"),
            "label_ids": request.data.get("label_ids", [])
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/bulk-operations", data=payload)
        return Response(result, status=result.get('status_code', 500))

class GmailWebhooksView(APIView):
    """Gmail webhooks management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id):
        """Get webhooks"""
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/webhooks")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id):
        """Create webhook"""
        payload = {
            "url": request.data.get("url"),
            "events": request.data.get("events", []),  # email_received, email_sent, email_opened, etc.
            "secret": request.data.get("secret"),
            "filters": request.data.get("filters", {})
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/webhooks", data=payload)
        return Response(result, status=result.get('status_code', 500))

class GmailWebhookView(APIView):
    """Single webhook management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id, webhook_id):
        """Get webhook details"""
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/webhooks/{webhook_id}")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def put(self, request, account_id, webhook_id):
        """Update webhook"""
        result = make_lunyamwi_gmail_request("PUT", f"/accounts/{account_id}/webhooks/{webhook_id}", data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def delete(self, request, account_id, webhook_id):
        """Delete webhook"""
        result = make_lunyamwi_gmail_request("DELETE", f"/accounts/{account_id}/webhooks/{webhook_id}")
        return Response(result, status=result.get('status_code', 500))


class GmailSearchView(APIView):
    """Gmail search functionality"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id):
        """Advanced email search"""
        payload = {
            "query": request.data.get("query"),
            "filters": request.data.get("filters", {
                "from": None,
                "to": None,
                "subject": None,
                "body_contains": None,
                "has_attachment": None,
                "date_range": {"start": None, "end": None},
                "folder": None,
                "labels": [],
                "is_read": None,
                "is_starred": None
            }),
            "sort_by": request.data.get("sort_by", "date"),  # date, relevance, from, subject
            "sort_order": request.data.get("sort_order", "desc"),  # asc, desc
            "limit": request.data.get("limit", 50),
            "cursor": request.data.get("cursor")
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/search", data=payload)
        return Response(result, status=result.get('status_code', 500))


class GmailUnsubscribeView(APIView):
    """Unsubscribe management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id):
        """Get unsubscribed contacts"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/unsubscribed", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id):
        """Add to unsubscribe list"""
        payload = {
            "email": request.data.get("email"),
            "reason": request.data.get("reason", "manual")
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/unsubscribed", data=payload)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def delete(self, request, account_id):
        """Remove from unsubscribe list"""
        payload = {
            "email": request.data.get("email")
        }
        
        result = make_lunyamwi_gmail_request("DELETE", f"/accounts/{account_id}/unsubscribed", data=payload)
        return Response(result, status=result.get('status_code', 500))


class GmailValidationView(APIView):
    """Email validation"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id):
        """Validate email addresses"""
        payload = {
            "emails": request.data.get("emails", []),
            "check_deliverability": request.data.get("check_deliverability", True),
            "check_disposable": request.data.get("check_disposable", True),
            "check_role_based": request.data.get("check_role_based", True)
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/validate", data=payload)
        return Response(result, status=result.get('status_code', 500))


class GmailBlacklistView(APIView):
    """Email blacklist management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id):
        """Get blacklisted emails/domains"""
        params = {
            'type': request.query_params.get('type'),  # email, domain
            'limit': request.query_params.get('limit', 50)
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_gmail_request("GET", f"/accounts/{account_id}/blacklist", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id):
        """Add to blacklist"""
        payload = {
            "email": request.data.get("email"),
            "domain": request.data.get("domain"),
            "reason": request.data.get("reason")
        }
        
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}/blacklist", data=payload)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def delete(self, request, account_id):
        """Remove from blacklist"""
        payload = {
            "email": request.data.get("email"),
            "domain": request.data.get("domain")
        }
        
        result = make_lunyamwi_gmail_request("DELETE", f"/accounts/{account_id}/blacklist", data=payload)
        return Response(result, status=result.get('status_code', 500))