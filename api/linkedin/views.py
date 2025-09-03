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

load_dotenv()

LUNYAMWI_LINKEDIN_BASE_URL = os.getenv("LUNYAMWI_LINKEDIN_BASE_URL", "https://example.com")
LUNYAMWI_LINKEDIN_API_KEY = os.getenv("LUNYAMWI_LINKEDIN_API_KEY")
LUNYAMWI_LINKEDIN_HEADERS = {
    "X-API-KEY": LUNYAMWI_LINKEDIN_API_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def make_lunyamwi_linkedin_request(method: str, endpoint: str, params: Dict = None, data: Dict = None, headers: Dict = None) -> Dict:
    """Helper function to make requests to API"""
    url = f"{LUNYAMWI_LINKEDIN_BASE_URL}{endpoint}"
    
    request_headers = LUNYAMWI_LINKEDIN_HEADERS.copy()
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

def handle_lunyamwi_linkedin_error(func):
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


class LinkedInAccountsView(APIView):
    """LinkedIn Accounts management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request):
        """Get all LinkedIn accounts"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'provider': 'linkedin'
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", "/accounts", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request):
        """Add LinkedIn account"""
        payload = {
            "provider": "linkedin",
            "name": request.data.get("name"),
            "username": request.data.get("username"),
            "password": request.data.get("password"),
            "proxy": request.data.get("proxy")
        }
        
        result = make_lunyamwi_linkedin_request("POST", "/accounts", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInAccountView(APIView):
    """Single LinkedIn Account management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get LinkedIn account details"""
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def put(self, request, account_id):
        """Update LinkedIn account"""
        result = make_lunyamwi_linkedin_request("PUT", f"/accounts/{account_id}", data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def delete(self, request, account_id):
        """Delete LinkedIn account"""
        result = make_lunyamwi_linkedin_request("DELETE", f"/accounts/{account_id}")
        return Response(result, status=result.get('status_code', 500))

class LinkedInAccountConnectView(APIView):
    """Connect LinkedIn account"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id):
        """Connect to LinkedIn account"""
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/connect", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class LinkedInAccountDisconnectView(APIView):
    """Disconnect LinkedIn account"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id):
        """Disconnect LinkedIn account"""
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/disconnect")
        return Response(result, status=result.get('status_code', 500))

class LinkedInChatsView(APIView):
    """LinkedIn Chats/Conversations"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get LinkedIn chats/conversations"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'unread_only': request.query_params.get('unread_only'),
            'search': request.query_params.get('search')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/chats", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id):
        """Create new LinkedIn chat"""
        payload = {
            "participants": request.data.get("participants"),  # List of LinkedIn user IDs
            "name": request.data.get("name"),  # Optional chat name
            "is_group": request.data.get("is_group", False)
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/chats", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInChatView(APIView):
    """Single LinkedIn Chat management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, chat_id):
        """Get specific LinkedIn chat"""
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/chats/{chat_id}")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def put(self, request, account_id, chat_id):
        """Update chat settings"""
        result = make_lunyamwi_linkedin_request("PUT", f"/accounts/{account_id}/chats/{chat_id}", data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def delete(self, request, account_id, chat_id):
        """Delete/Leave chat"""
        result = make_lunyamwi_linkedin_request("DELETE", f"/accounts/{account_id}/chats/{chat_id}")
        return Response(result, status=result.get('status_code', 500))

class LinkedInMessagesView(APIView):
    """LinkedIn Messages management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, chat_id):
        """Get messages from a LinkedIn chat"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'since': request.query_params.get('since'),
            'until': request.query_params.get('until'),
            'search': request.query_params.get('search')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/chats/{chat_id}/messages", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id, chat_id):
        """Send message to LinkedIn chat"""
        payload = {
            "text": request.data.get("text"),
            "attachments": request.data.get("attachments", []),
            "reply_to": request.data.get("reply_to"),  # Message ID to reply to
            "mentions": request.data.get("mentions", []),  # List of user IDs to mention
            "scheduled_at": request.data.get("scheduled_at")  # ISO datetime string
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/chats/{chat_id}/messages", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInMessageView(APIView):
    """Single LinkedIn Message management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, message_id):
        """Get specific LinkedIn message"""
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/messages/{message_id}")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def put(self, request, account_id, message_id):
        """Update LinkedIn message (edit)"""
        payload = {
            "text": request.data.get("text"),
            "attachments": request.data.get("attachments", [])
        }
        
        result = make_lunyamwi_linkedin_request("PUT", f"/accounts/{account_id}/messages/{message_id}", data=payload)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def delete(self, request, account_id, message_id):
        """Delete LinkedIn message"""
        result = make_lunyamwi_linkedin_request("DELETE", f"/accounts/{account_id}/messages/{message_id}")
        return Response(result, status=result.get('status_code', 500))

class LinkedInMessageReactionView(APIView):
    """LinkedIn Message reactions"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id, message_id):
        """Add reaction to message"""
        payload = {
            "emoji": request.data.get("emoji", "👍")
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/messages/{message_id}/reactions", data=payload)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def delete(self, request, account_id, message_id):
        """Remove reaction from message"""
        result = make_lunyamwi_linkedin_request("DELETE", f"/accounts/{account_id}/messages/{message_id}/reactions")
        return Response(result, status=result.get('status_code', 500))

class LinkedInBulkMessagesView(APIView):
    """Send bulk messages on LinkedIn"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id):
        """Send bulk messages"""
        payload = {
            "messages": request.data.get("messages"),  # List of message objects
            "delay_between_messages": request.data.get("delay_between_messages", 1),  # Seconds
            "personalize": request.data.get("personalize", True)
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/messages/bulk", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInPostsView(APIView):
    """LinkedIn Posts management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get LinkedIn posts"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'author_id': request.query_params.get('author_id'),
            'since': request.query_params.get('since'),
            'until': request.query_params.get('until'),
            'include_comments': request.query_params.get('include_comments', 'false'),
            'include_reactions': request.query_params.get('include_reactions', 'false')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/posts", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id):
        """Create LinkedIn post"""
        payload = {
            "text": request.data.get("text"),
            "visibility": request.data.get("visibility", "PUBLIC"),  # PUBLIC, CONNECTIONS, PRIVATE
            "attachments": request.data.get("attachments", []),
            "poll": request.data.get("poll"),  # Poll object
            "scheduled_at": request.data.get("scheduled_at"),  # ISO datetime string
            "tags": request.data.get("tags", []),  # Hashtags
            "mentions": request.data.get("mentions", []),  # User mentions
            "location": request.data.get("location"),  # Location object
            "article": request.data.get("article"),  # Article object for LinkedIn articles
            "company_id": request.data.get("company_id")  # Post as company page
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/posts", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInPostView(APIView):
    """Single LinkedIn Post management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, post_id):
        """Get specific LinkedIn post"""
        params = {
            'include_comments': request.query_params.get('include_comments', 'false'),
            'include_reactions': request.query_params.get('include_reactions', 'false'),
            'include_analytics': request.query_params.get('include_analytics', 'false')
        }
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/posts/{post_id}", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def put(self, request, account_id, post_id):
        """Update LinkedIn post"""
        payload = {
            "text": request.data.get("text"),
            "visibility": request.data.get("visibility"),
            "attachments": request.data.get("attachments"),
            "tags": request.data.get("tags"),
            "location": request.data.get("location")
        }
        
        result = make_lunyamwi_linkedin_request("PUT", f"/accounts/{account_id}/posts/{post_id}", data=payload)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def delete(self, request, account_id, post_id):
        """Delete LinkedIn post"""
        result = make_lunyamwi_linkedin_request("DELETE", f"/accounts/{account_id}/posts/{post_id}")
        return Response(result, status=result.get('status_code', 500))

class LinkedInPostLikesView(APIView):
    """LinkedIn Post likes/reactions management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, post_id):
        """Get post likes/reactions"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'reaction_type': request.query_params.get('reaction_type')  # LIKE, LOVE, CELEBRATE, etc.
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/posts/{post_id}/reactions", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id, post_id):
        """Like/React to LinkedIn post"""
        payload = {
            "reaction_type": request.data.get("reaction_type", "LIKE")  # LIKE, LOVE, CELEBRATE, SUPPORT, INSIGHTFUL, FUNNY
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/posts/{post_id}/reactions", data=payload)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def delete(self, request, account_id, post_id):
        """Unlike LinkedIn post"""
        result = make_lunyamwi_linkedin_request("DELETE", f"/accounts/{account_id}/posts/{post_id}/reactions")
        return Response(result, status=result.get('status_code', 500))

class LinkedInPostCommentsView(APIView):
    """LinkedIn Post comments management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, post_id):
        """Get post comments"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'include_replies': request.query_params.get('include_replies', 'true'),
            'sort_order': request.query_params.get('sort_order', 'CHRONOLOGICAL')  # CHRONOLOGICAL, RELEVANCE
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/posts/{post_id}/comments", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id, post_id):
        """Comment on LinkedIn post"""
        payload = {
            "text": request.data.get("text"),
            "attachments": request.data.get("attachments", []),
            "mentions": request.data.get("mentions", []),
            "parent_comment_id": request.data.get("parent_comment_id")  # For replies
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/posts/{post_id}/comments", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInCommentView(APIView):
    """LinkedIn Comment management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, comment_id):
        """Get specific comment"""
        params = {
            'include_replies': request.query_params.get('include_replies', 'true'),
            'include_reactions': request.query_params.get('include_reactions', 'false')
        }
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/comments/{comment_id}", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def put(self, request, account_id, comment_id):
        """Update comment"""
        payload = {
            "text": request.data.get("text"),
            "attachments": request.data.get("attachments")
        }
        
        result = make_lunyamwi_linkedin_request("PUT", f"/accounts/{account_id}/comments/{comment_id}", data=payload)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def delete(self, request, account_id, comment_id):
        """Delete comment"""
        result = make_lunyamwi_linkedin_request("DELETE", f"/accounts/{account_id}/comments/{comment_id}")
        return Response(result, status=result.get('status_code', 500))

class LinkedInCommentReactionsView(APIView):
    """LinkedIn Comment reactions"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id, comment_id):
        """React to comment"""
        payload = {
            "reaction_type": request.data.get("reaction_type", "LIKE")
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/comments/{comment_id}/reactions", data=payload)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def delete(self, request, account_id, comment_id):
        """Remove reaction from comment"""
        result = make_lunyamwi_linkedin_request("DELETE", f"/accounts/{account_id}/comments/{comment_id}/reactions")
        return Response(result, status=result.get('status_code', 500))

class LinkedInPostShareView(APIView):
    """Share LinkedIn posts"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id, post_id):
        """Share/Repost LinkedIn post"""
        payload = {
            "comment": request.data.get("comment"),  # Optional comment when sharing
            "visibility": request.data.get("visibility", "PUBLIC")
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/posts/{post_id}/share", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInMediaView(APIView):
    """LinkedIn Media management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id):
        """Upload media to LinkedIn"""
        payload = {
            "file_url": request.data.get("file_url"),
            "file_base64": request.data.get("file_base64"),
            "file_type": request.data.get("file_type"),  # IMAGE, VIDEO, DOCUMENT
            "description": request.data.get("description"),
            "title": request.data.get("title")
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/media", data=payload)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, media_id):
        """Get LinkedIn media"""
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/media/{media_id}")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def delete(self, request, account_id, media_id):
        """Delete LinkedIn media"""
        result = make_lunyamwi_linkedin_request("DELETE", f"/accounts/{account_id}/media/{media_id}")
        return Response(result, status=result.get('status_code', 500))

class LinkedInProfileView(APIView):
    """LinkedIn Profile management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get LinkedIn profile"""
        params = {
            'include_connections': request.query_params.get('include_connections', 'false'),
            'include_activity': request.query_params.get('include_activity', 'false')
        }
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/profile", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def put(self, request, account_id):
        """Update LinkedIn profile"""
        payload = {
            "headline": request.data.get("headline"),
            "summary": request.data.get("summary"),
            "location": request.data.get("location"),
            "industry": request.data.get("industry"),
            "skills": request.data.get("skills", []),
            "experience": request.data.get("experience", []),
            "education": request.data.get("education", [])
        }
        
        result = make_lunyamwi_linkedin_request("PUT", f"/accounts/{account_id}/profile", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInProfileSearchView(APIView):
    """Search LinkedIn profiles"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id):
        """Search LinkedIn profiles"""
        payload = {
            "keywords": request.data.get("keywords"),
            "location": request.data.get("location"),
            "industry": request.data.get("industry"),
            "company": request.data.get("company"),
            "school": request.data.get("school"),
            "current_company": request.data.get("current_company"),
            "past_company": request.data.get("past_company"),
            "connections": request.data.get("connections"),  # 1st, 2nd, 3rd+
            "limit": request.data.get("limit", 50),
            "cursor": request.data.get("cursor")
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/profile/search", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInProfileByUrlView(APIView):
    """Get LinkedIn profile by URL"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id):
        """Get LinkedIn profile by profile URL"""
        payload = {
            "profile_url": request.data.get("profile_url"),
            "include_contact_info": request.data.get("include_contact_info", False),
            "include_activity": request.data.get("include_activity", False)
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/profile/by-url", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInConnectionsView(APIView):
    """LinkedIn Connections management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get LinkedIn connections"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'search': request.query_params.get('search'),
            'include_contact_info': request.query_params.get('include_contact_info', 'false')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/connections", params=params)
        return Response(result, status=result.get('status_code', 500))

class LinkedInConnectionInvitationsView(APIView):
    """LinkedIn Connection invitations"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get connection invitations"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'type': request.query_params.get('type'),  # sent, received
            'status': request.query_params.get('status')  # pending, accepted, declined
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/connection-invitations", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id):
        """Send connection invitation"""
        payload = {
            "profile_id": request.data.get("profile_id"),
            "profile_url": request.data.get("profile_url"),
            "message": request.data.get("message"),
            "note": request.data.get("note")
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/connection-invitations", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInConnectionInvitationView(APIView):
    """Single LinkedIn Connection invitation"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, invitation_id):
        """Get specific connection invitation"""
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/connection-invitations/{invitation_id}")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def put(self, request, account_id, invitation_id):
        """Accept/decline connection invitation"""
        payload = {
            "action": request.data.get("action")  # accept, decline
        }
        
        result = make_lunyamwi_linkedin_request("PUT", f"/accounts/{account_id}/connection-invitations/{invitation_id}", data=payload)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def delete(self, request, account_id, invitation_id):
        """Withdraw connection invitation"""
        result = make_lunyamwi_linkedin_request("DELETE", f"/accounts/{account_id}/connection-invitations/{invitation_id}")
        return Response(result, status=result.get('status_code', 500))

class LinkedInCompaniesView(APIView):
    """LinkedIn Companies"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get followed companies"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/companies", params=params)
        return Response(result, status=result.get('status_code', 500))

class LinkedInCompanyView(APIView):
    """LinkedIn Company management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, company_id):
        """Get LinkedIn company profile"""
        params = {
            'include_posts': request.query_params.get('include_posts', 'false'),
            'include_employees': request.query_params.get('include_employees', 'false')
        }
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/companies/{company_id}", params=params)
        return Response(result, status=result.get('status_code', 500))

class LinkedInCompanySearchView(APIView):
    """Search LinkedIn companies"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id):
        """Search LinkedIn companies"""
        payload = {
            "keywords": request.data.get("keywords"),
            "industry": request.data.get("industry"),
            "location": request.data.get("location"),
            "company_size": request.data.get("company_size"),
            "limit": request.data.get("limit", 50),
            "cursor": request.data.get("cursor")
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/companies/search", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInCompanyFollowView(APIView):
    """Follow/unfollow LinkedIn company"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id, company_id):
        """Follow LinkedIn company"""
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/companies/{company_id}/follow")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def delete(self, request, account_id, company_id):
        """Unfollow LinkedIn company"""
        result = make_lunyamwi_linkedin_request("DELETE", f"/accounts/{account_id}/companies/{company_id}/follow")
        return Response(result, status=result.get('status_code', 500))

class LinkedInAnalyticsView(APIView):
    """LinkedIn Analytics"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get LinkedIn analytics"""
        params = {
            'start_date': request.query_params.get('start_date'),
            'end_date': request.query_params.get('end_date'),
            'metrics': request.query_params.get('metrics'),  # impressions, clicks, likes, comments, shares
            'granularity': request.query_params.get('granularity', 'day')  # day, week, month
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/analytics", params=params)
        return Response(result, status=result.get('status_code', 500))

class LinkedInPostAnalyticsView(APIView):
    """LinkedIn Post Analytics"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, post_id):
        """Get post analytics"""
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/posts/{post_id}/analytics")
        return Response(result, status=result.get('status_code', 500))

class LinkedInAutomationTasksView(APIView):
    """LinkedIn Automation Tasks"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get automation tasks"""
        params = {
            'status': request.query_params.get('status'),  # active, paused, completed
            'type': request.query_params.get('type'),  # messaging, posting, connection
            'limit': request.query_params.get('limit', 50)
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/automation/tasks", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id):
        """Create automation task"""
        payload = {
            "type": request.data.get("type"),  # messaging_campaign, post_schedule, connection_campaign
            "name": request.data.get("name"),
            "configuration": request.data.get("configuration"),
            "schedule": request.data.get("schedule"),
            "target_criteria": request.data.get("target_criteria"),
            "enabled": request.data.get("enabled", True)
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/automation/tasks", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInAutomationTaskView(APIView):
    """Single LinkedIn Automation Task"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, task_id):
        """Get automation task details"""
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/automation/tasks/{task_id}")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def put(self, request, account_id, task_id):
        """Update automation task"""
        result = make_lunyamwi_linkedin_request("PUT", f"/accounts/{account_id}/automation/tasks/{task_id}", data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def delete(self, request, account_id, task_id):
        """Delete automation task"""
        result = make_lunyamwi_linkedin_request("DELETE", f"/accounts/{account_id}/automation/tasks/{task_id}")
        return Response(result, status=result.get('status_code', 500))
    


class LinkedInFeedView(APIView):
    """LinkedIn Feed management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get LinkedIn feed"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'sort_by': request.query_params.get('sort_by', 'RELEVANCE'),  # RELEVANCE, RECENCY
            'include_promoted': request.query_params.get('include_promoted', 'true')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/feed", params=params)
        return Response(result, status=result.get('status_code', 500))

class LinkedInNotificationsView(APIView):
    """LinkedIn Notifications"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get notifications"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'unread_only': request.query_params.get('unread_only', 'false'),
            'type': request.query_params.get('type')  # CONNECTION, MESSAGE, PROFILE_VIEW, etc.
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/notifications", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def put(self, request, account_id):
        """Mark notifications as read"""
        payload = {
            "notification_ids": request.data.get("notification_ids", []),
            "mark_all": request.data.get("mark_all", False)
        }
        
        result = make_lunyamwi_linkedin_request("PUT", f"/accounts/{account_id}/notifications/mark-read", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInGroupsView(APIView):
    """LinkedIn Groups management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get joined groups"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/groups", params=params)
        return Response(result, status=result.get('status_code', 500))

class LinkedInGroupView(APIView):
    """Single LinkedIn Group management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, group_id):
        """Get group details"""
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/groups/{group_id}")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id, group_id):
        """Join group"""
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/groups/{group_id}/join")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def delete(self, request, account_id, group_id):
        """Leave group"""
        result = make_lunyamwi_linkedin_request("DELETE", f"/accounts/{account_id}/groups/{group_id}/leave")
        return Response(result, status=result.get('status_code', 500))

class LinkedInGroupPostsView(APIView):
    """LinkedIn Group Posts"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, group_id):
        """Get group posts"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/groups/{group_id}/posts", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id, group_id):
        """Post to group"""
        payload = {
            "text": request.data.get("text"),
            "attachments": request.data.get("attachments", []),
            "title": request.data.get("title")
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/groups/{group_id}/posts", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInEventsView(APIView):
    """LinkedIn Events management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get events"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'type': request.query_params.get('type'),  # attending, interested, created
            'upcoming_only': request.query_params.get('upcoming_only', 'true')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/events", params=params)
        return Response(result, status=result.get('status_code', 500))

class LinkedInEventView(APIView):
    """Single LinkedIn Event management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, event_id):
        """Get event details"""
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/events/{event_id}")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id, event_id):
        """RSVP to event"""
        payload = {
            "status": request.data.get("status")  # ATTENDING, INTERESTED, NOT_ATTENDING
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/events/{event_id}/rsvp", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInNewslettersView(APIView):
    """LinkedIn Newsletters"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get newsletters"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'type': request.query_params.get('type')  # subscribed, created
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/newsletters", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id):
        """Create newsletter"""
        payload = {
            "title": request.data.get("title"),
            "description": request.data.get("description"),
            "frequency": request.data.get("frequency"),  # WEEKLY, BIWEEKLY, MONTHLY
            "cover_image": request.data.get("cover_image")
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/newsletters", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInNewsletterView(APIView):
    """Single LinkedIn Newsletter management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, newsletter_id):
        """Get newsletter details"""
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/newsletters/{newsletter_id}")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def put(self, request, account_id, newsletter_id):
        """Update newsletter"""
        result = make_lunyamwi_linkedin_request("PUT", f"/accounts/{account_id}/newsletters/{newsletter_id}", data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id, newsletter_id):
        """Subscribe/unsubscribe to newsletter"""
        payload = {
            "action": request.data.get("action")  # subscribe, unsubscribe
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/newsletters/{newsletter_id}/subscription", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInNewsletterArticlesView(APIView):
    """LinkedIn Newsletter Articles"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, newsletter_id):
        """Get newsletter articles"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/newsletters/{newsletter_id}/articles", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id, newsletter_id):
        """Publish newsletter article"""
        payload = {
            "title": request.data.get("title"),
            "content": request.data.get("content"),
            "cover_image": request.data.get("cover_image"),
            "publish_immediately": request.data.get("publish_immediately", True)
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/newsletters/{newsletter_id}/articles", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInArticlesView(APIView):
    """LinkedIn Articles management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get published articles"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'author_id': request.query_params.get('author_id')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/articles", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id):
        """Publish article"""
        payload = {
            "title": request.data.get("title"),
            "content": request.data.get("content"),
            "cover_image": request.data.get("cover_image"),
            "tags": request.data.get("tags", []),
            "publish_date": request.data.get("publish_date"),
            "is_draft": request.data.get("is_draft", False)
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/articles", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInArticleView(APIView):
    """Single LinkedIn Article management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, article_id):
        """Get article details"""
        params = {
            'include_analytics': request.query_params.get('include_analytics', 'false')
        }
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/articles/{article_id}", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def put(self, request, account_id, article_id):
        """Update article"""
        result = make_lunyamwi_linkedin_request("PUT", f"/accounts/{account_id}/articles/{article_id}", data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def delete(self, request, account_id, article_id):
        """Delete article"""
        result = make_lunyamwi_linkedin_request("DELETE", f"/accounts/{account_id}/articles/{article_id}")
        return Response(result, status=result.get('status_code', 500))

class LinkedInSkillsView(APIView):
    """LinkedIn Skills management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get profile skills"""
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/skills")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id):
        """Add skill"""
        payload = {
            "skill_name": request.data.get("skill_name"),
            "proficiency": request.data.get("proficiency")  # BEGINNER, INTERMEDIATE, ADVANCED, EXPERT
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/skills", data=payload)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def delete(self, request, account_id, skill_id):
        """Remove skill"""
        result = make_lunyamwi_linkedin_request("DELETE", f"/accounts/{account_id}/skills/{skill_id}")
        return Response(result, status=result.get('status_code', 500))

class LinkedInEndorsementsView(APIView):
    """LinkedIn Endorsements"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get endorsements"""
        params = {
            'skill_id': request.query_params.get('skill_id'),
            'limit': request.query_params.get('limit', 50)
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/endorsements", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id):
        """Endorse skill"""
        payload = {
            "profile_id": request.data.get("profile_id"),
            "skill_id": request.data.get("skill_id")
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/endorsements", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInRecommendationsView(APIView):
    """LinkedIn Recommendations"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get recommendations"""
        params = {
            'type': request.query_params.get('type'),  # received, given
            'limit': request.query_params.get('limit', 50)
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/recommendations", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id):
        """Write recommendation"""
        payload = {
            "profile_id": request.data.get("profile_id"),
            "relationship": request.data.get("relationship"),
            "text": request.data.get("text"),
            "position_title": request.data.get("position_title")
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/recommendations", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInSavedPostsView(APIView):
    """LinkedIn Saved Posts"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get saved posts"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/saved-posts", params=params)
        return Response(result, status=result.get('status_code', 500))

class LinkedInSavedPostView(APIView):
    """Save/unsave LinkedIn posts"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id, post_id):
        """Save post"""
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/posts/{post_id}/save")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def delete(self, request, account_id, post_id):
        """Unsave post"""
        result = make_lunyamwi_linkedin_request("DELETE", f"/accounts/{account_id}/posts/{post_id}/save")
        return Response(result, status=result.get('status_code', 500))

class LinkedInHashtagsView(APIView):
    """LinkedIn Hashtags"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get followed hashtags"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/hashtags", params=params)
        return Response(result, status=result.get('status_code', 500))

class LinkedInHashtagView(APIView):
    """LinkedIn Hashtag management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, hashtag):
        """Get hashtag details and posts"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/hashtags/{hashtag}", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id, hashtag):
        """Follow hashtag"""
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/hashtags/{hashtag}/follow")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def delete(self, request, account_id, hashtag):
        """Unfollow hashtag"""
        result = make_lunyamwi_linkedin_request("DELETE", f"/accounts/{account_id}/hashtags/{hashtag}/follow")
        return Response(result, status=result.get('status_code', 500))

class LinkedInInfluencersView(APIView):
    """LinkedIn Influencers"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get followed influencers"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/influencers", params=params)
        return Response(result, status=result.get('status_code', 500))

class LinkedInInfluencerView(APIView):
    """LinkedIn Influencer management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id, influencer_id):
        """Follow influencer"""
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/influencers/{influencer_id}/follow")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def delete(self, request, account_id, influencer_id):
        """Unfollow influencer"""
        result = make_lunyamwi_linkedin_request("DELETE", f"/accounts/{account_id}/influencers/{influencer_id}/follow")
        return Response(result, status=result.get('status_code', 500))

class LinkedInLearningView(APIView):
    """LinkedIn Learning"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get learning courses and certificates"""
        params = {
            'type': request.query_params.get('type'),  # completed, in_progress, saved
            'limit': request.query_params.get('limit', 50)
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/learning", params=params)
        return Response(result, status=result.get('status_code', 500))

class LinkedInJobsView(APIView):
    """LinkedIn Jobs"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get job recommendations and applications"""
        params = {
            'type': request.query_params.get('type'),  # recommendations, applications, saved
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/jobs", params=params)
        return Response(result, status=result.get('status_code', 500))

class LinkedInJobView(APIView):
    """LinkedIn Job management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, job_id):
        """Get job details"""
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/jobs/{job_id}")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id, job_id):
        """Apply to job or save job"""
        payload = {
            "action": request.data.get("action"),  # apply, save
            "cover_letter": request.data.get("cover_letter"),
            "resume": request.data.get("resume")
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/jobs/{job_id}/action", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInLiveVideoView(APIView):
    """LinkedIn Live Video"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id):
        """Start live video"""
        payload = {
            "title": request.data.get("title"),
            "description": request.data.get("description"),
            "visibility": request.data.get("visibility", "PUBLIC")
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/live-video/start", data=payload)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def delete(self, request, account_id, video_id):
        """End live video"""
        result = make_lunyamwi_linkedin_request("DELETE", f"/accounts/{account_id}/live-video/{video_id}/end")
        return Response(result, status=result.get('status_code', 500))


class LinkedInWebhooksView(APIView):
    """LinkedIn Webhooks management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get webhooks"""
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/webhooks")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id):
        """Create webhook"""
        payload = {
            "url": request.data.get("url"),
            "events": request.data.get("events", []),  # message_received, post_created, etc.
            "secret": request.data.get("secret")
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}/webhooks", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInWebhookView(APIView):
    """Single LinkedIn Webhook"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, webhook_id):
        """Get webhook details"""
        result = make_lunyamwi_linkedin_request("GET", f"/accounts/{account_id}/webhooks/{webhook_id}")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def put(self, request, account_id, webhook_id):
        """Update webhook"""
        result = make_lunyamwi_linkedin_request("PUT", f"/accounts/{account_id}/webhooks/{webhook_id}", data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def delete(self, request, account_id, webhook_id):
        """Delete webhook"""
        result = make_lunyamwi_linkedin_request("DELETE", f"/accounts/{account_id}/webhooks/{webhook_id}")
        return Response(result, status=result.get('status_code', 500))