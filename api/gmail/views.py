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
from urllib.parse import unquote
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


class GmailAuthURLView(APIView):
    """Generate Gmail OAuth URL"""
    permission_classes = [AllowAny]

    @handle_lunyamwi_gmail_error
    def get(self, request):
        """Get OAuth URL"""
        client_id = os.getenv("GMAIL_CLIENT_ID", "")
        redirect_uri = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:8000/auth/callback")
        scope = "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.modify"
        
        if not client_id:
            return Response({
                "error": "GMAIL_CLIENT_ID not configured",
                "error_code": "config_error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
            "access_type": "offline",
            "prompt": "consent"
        }
        auth_url = f"https://accounts.google.com/o/oauth2/auth?{requests.compat.urlencode(params)}"
        
        return Response({
            "auth_url": auth_url
        }, status=status.HTTP_200_OK)

class GmailOAuthCallbackView(APIView):
    """Handle Gmail OAuth callback"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request):
        """Handle OAuth callback"""
        code = unquote(request.query_params.get("code", ""))
        redirect_uri = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:8000/auth/callback")
        client_id = os.getenv("GMAIL_CLIENT_ID", "")
        client_secret = os.getenv("GMAIL_CLIENT_SECRET", "")
        
        if not code:
            return Response({
                "error": "Authorization code is required",
                "error_code": "invalid_request"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not client_id or not client_secret:
            return Response({
                "error": "GMAIL_CLIENT_ID or GMAIL_CLIENT_SECRET not configured",
                "error_code": "config_error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        
        response = requests.post(token_url, data=data)
        if response.status_code != 200:
            return Response({
                "error": "Failed to exchange code for tokens",
                "details": response.json(),
                "error_code": "token_exchange_failed"
            }, status=response.status_code)
        
        tokens = response.json()
        return Response(tokens, status=status.HTTP_200_OK)

    

class GmailAccountConnectView(APIView):
    """Connect Gmail account"""
    permission_classes = [AllowAny]

    @handle_lunyamwi_gmail_error
    def post(self, request):
        """Connect to Gmail account"""
        payload = {
            "provider": "GOOGLE_OAUTH",
            "refresh_token": request.data.get("refresh_token", ""),
            "access_token": request.data.get("access_token", "")
        }
    
        result = make_lunyamwi_gmail_request("POST", "/accounts", data=payload)
        return Response(result, status=result.get('status_code', 500))

class GmailAccountReconnectView(APIView):
    """Reconnect Gmail account with new tokens"""
    permission_classes = [AllowAny]

    @handle_lunyamwi_gmail_error
    def post(self, request, account_id):
        """Reconnect Gmail account"""
        payload = {
            "provider": "GOOGLE_OAUTH",
            "account_id": account_id,
            "refresh_token": request.data.get("refresh_token", ""),
            "access_token": request.data.get("access_token", "")
        }
    
        result = make_lunyamwi_gmail_request("POST", f"/accounts/{account_id}", data=payload)
        return Response(result, status=result.get('status_code', 500))
    
class GmailEmailsView(APIView):
    """Gmail Emails management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id):
        """Get emails from Gmail"""
        params = {
            'account_id': account_id,
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
        
        result = make_lunyamwi_gmail_request("GET", f"/emails", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id):
        """Send email via Gmail"""
        payload = {
            "account_id": account_id,
            "to": [
                {"display_name": name, "identifier": email}
                for name, email in request.data.get("to", [])
            ],
            "cc": [
                {"display_name": name, "identifier": email}
                for name, email in request.data.get("cc", [])
            ],
            "bcc": [
                {"display_name": name, "identifier": email}
                for name, email in request.data.get("bcc", [])
            ],
            "subject": request.data.get("subject"),
            "body": request.data.get("body"),
            "body_type": request.data.get("body_type", "html"),  # html, plain
            "attachments": request.data.get("attachments", []),
            # "reply_to": request.data.get("reply_to"),
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

        result = make_lunyamwi_gmail_request("POST", f"/emails", data=payload)
        return Response(result, status=result.get('status_code', 500))

class GmailEmailView(APIView):
    """Single Gmail Email management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id, email_id):
        """Get specific email"""
        params = {
            'account_id': account_id,
            'include_thread': request.query_params.get('include_thread', 'false'),
            'include_attachments': request.query_params.get('include_attachments', 'true'),
            'mark_as_read': request.query_params.get('mark_as_read', 'false')
        }
        
        result = make_lunyamwi_gmail_request("GET", f"/emails/{email_id}", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def put(self, request, account_id, email_id):
        """Update email (mark as read/unread, add labels, etc.)"""
        payload = {
            "account_id": account_id,
            "unread": request.data.get("unread",False),
            "is_read": request.data.get("is_read"),
            "is_starred": request.data.get("is_starred"),
            "is_important": request.data.get("is_important"),
            "labels": request.data.get("labels"),  # Add/remove labels
            "folders": request.data.get("folders", []),  # Move to folder
            "category": request.data.get("category")
        }

        result = make_lunyamwi_gmail_request("PUT", f"/emails/{email_id}", data=payload)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def delete(self, request, account_id, email_id):
        """Delete email (move to trash or permanent delete)"""
        params = {
            'account_id': account_id,
            'permanent': request.query_params.get('permanent', 'false')
        }
        
        result = make_lunyamwi_gmail_request("DELETE", f"/emails/{email_id}", params=params)
        return Response(result, status=result.get('status_code', 500))

class GmailRetrieveAttachmentView(APIView):
    """Retrieve Gmail email attachment"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id, email_id, attachment_id):
        """Get email attachment"""
        params = {
            'account_id': account_id,
            'email_id': email_id,
            'attachment_id': attachment_id
        }
        
        result = make_lunyamwi_gmail_request("GET", f"/emails/{email_id}/attachments/{attachment_id}", params=params)
        return Response(result, status=result.get('status_code', 500))


class GmailListFoldersView(APIView):
    """List Gmail folders/labels"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id):
        """Get folders/labels"""
        params = {
            'account_id': account_id
        }
        
        result = make_lunyamwi_gmail_request("GET", f"/folders", params=params)
        return Response(result, status=result.get('status_code', 500))
    

class GmailFolderView(APIView):
    """Single Gmail folder/label management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id, folder_id):
        """Get folder/label details"""
        params = {
            'account_id': account_id
        }
        
        result = make_lunyamwi_gmail_request("GET", f"/folders/{folder_id}", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    
class GmailCreateDraftView(APIView):
    """Create Gmail draft"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id):
        """Create draft email"""
        payload = {
            "account_id": account_id,
            "to": [
                {
                    "display_name": request.data.get("to_name", ""),
                    "identifier": request.data.get("to_email", "")
                }
            ],
            "body": request.data.get("body", ""),
            "subject": request.data.get("subject", "")
        }

        result = make_lunyamwi_gmail_request("POST", f"/drafts", data=payload)
        return Response(result, status=result.get('status_code', 500))


class GmailWebhooksView(APIView):
    """Gmail webhooks management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id):
        """Get webhooks"""
        params = {
            'account_id': account_id
        }
        result = make_lunyamwi_gmail_request("GET", f"/webhooks", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def post(self, request, account_id):
        """Create webhook"""
        payload = {
            'account_id': account_id,
            "url": request.data.get("url"),
            "events": request.data.get("events", []),  # email_received, email_sent, email_opened, etc.
            "secret": request.data.get("secret"),
            "filters": request.data.get("filters", {})
        }

        result = make_lunyamwi_gmail_request("POST", f"/webhooks", data=payload)
        return Response(result, status=result.get('status_code', 500))

class GmailWebhookView(APIView):
    """Single webhook management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_gmail_error
    def get(self, request, account_id, webhook_id):
        """Get webhook details"""
        params = {
            'account_id': account_id
        }
        result = make_lunyamwi_gmail_request("GET", f"/webhooks/{webhook_id}", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def put(self, request, account_id, webhook_id):
        """Update webhook"""
        params = {
            'account_id': account_id
        }
        result = make_lunyamwi_gmail_request("PUT", f"/webhooks/{webhook_id}", params=params, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_gmail_error
    def delete(self, request, account_id, webhook_id):
        """Delete webhook"""
        params = {
            'account_id': account_id
        }
        result = make_lunyamwi_gmail_request("DELETE", f"/webhooks/{webhook_id}", params=params)
        return Response(result, status=result.get('status_code', 500))


