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
            'provider': 'LINKEDIN'
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", "/accounts", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request):
        """Add LinkedIn account"""
        payload = {
            "provider": "LINKEDIN",
            "name": request.data.get("name"),
            "username": request.data.get("username"),
            "password": request.data.get("password"),
            "country": request.data.get("country", "US"),
            "city": request.data.get("city", ""),
            "proxy": {
                "protocol": "https",
                "host": "gate.decodo.com",
                "port": 10001,
                "username": f"user-{os.getenv("PROXY_USERNAME", "")}-country-{request.data.get("country", "")}-city-{request.data.get("city", "")}",
                "password": os.getenv("PROXY_PASSWORD", "")
            }
        }
        
        result = make_lunyamwi_linkedin_request("POST", "/accounts", data=payload)
            
        return Response(result, status=result.get('status_code', 500))

class LinkedInSolveCheckpointView(APIView):
    """Solve LinkedIn checkpoint (2FA)"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def post(self, request):
        """Submit 2FA code to solve checkpoint"""
        payload = {
            "provider": "LINKEDIN",
            "account_id": request.data.get("account_id", ""),
            "code": request.data.get("code", "")
        }
        result = make_lunyamwi_linkedin_request("POST", "/accounts/checkpoint", data=payload)
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
    def post(self, request, account_id):
        """Update LinkedIn account details"""
        payload = {
            "provider": "LINKEDIN",
            "name": request.data.get("name", ""),
            "username": request.data.get("username", ""),
            "password": request.data.get("password", ""),
            "country": request.data.get("country", ""),
            "city": request.data.get("city", ""),
            "proxy": {
                "protocol": "https",
                "host": "gate.decodo.com",
                "port": 10001,
                "username": f"user-{os.getenv("PROXY_USERNAME", "")}-country-{request.data.get("country", "")}-city-{request.data.get("city", "")}",
                "password": os.getenv("PROXY_PASSWORD", "")
            }
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("POST", f"/accounts/{account_id}", data=payload)
        return Response(result, status=result.get('status_code', 500))

    @handle_lunyamwi_linkedin_error
    def delete(self, request, account_id):
        """Delete LinkedIn account"""
        result = make_lunyamwi_linkedin_request("DELETE", f"/accounts/{account_id}")
        return Response(result, status=result.get('status_code', 500))


class LinkedInChatsView(APIView):
    """LinkedIn Chats/Conversations"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get LinkedIn chats/conversations"""
        params = {
            'account_type': 'LINKEDIN',
            'account_id': account_id
        }
        params = {k: v for k, v in params.items() if v is not None}

        result = make_lunyamwi_linkedin_request("GET", f"/chats", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id):
        """Create new LinkedIn chat"""
        payload = {
            "text": request.data.get("text"),
            "attendees_ids": request.data.get("attendees_ids"),  # List of LinkedIn user IDs
            "account_id": account_id,  # Optional chat name
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/chats", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInChatView(APIView):
    """Single LinkedIn Chat management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, chat_id):
        """Get specific LinkedIn chat"""
        params = {
            'account_id': account_id
        }
        result = make_lunyamwi_linkedin_request("GET", f"/chats/{chat_id}", params=params)
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
        
        result = make_lunyamwi_linkedin_request("GET", f"/chats/{chat_id}/messages", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id, chat_id):
        """Send message to LinkedIn chat"""
        payload = {
            "account_id": account_id,
            "text": request.data.get("text"),
            "attachments": request.data.get("attachments", []),
            "reply_to": request.data.get("reply_to"),  # Message ID to reply to
            "mentions": request.data.get("mentions", []),  # List of user IDs to mention
            "scheduled_at": request.data.get("scheduled_at")  # ISO datetime string
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/chats/{chat_id}/messages", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInListAttendeesChatView(APIView):
    """List attendees of a LinkedIn chat"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, chat_id):
        """Get attendees of a LinkedIn chat"""
        params = {
            'account_id': account_id
        }
        result = make_lunyamwi_linkedin_request("GET", f"/chats/{chat_id}/attendees", params=params)
        return Response(result, status=result.get('status_code', 500))

class LinkedInChatSyncView(APIView):
    """Manage attendees of a LinkedIn chat"""
    permission_classes = [AllowAny]

    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, chat_id):
        """Get Chat to be synced"""
        params = {
            'account_id': account_id
        }
        result = make_lunyamwi_linkedin_request("GET", f"/chats/{chat_id}/sync", params=params)
        return Response(result, status=result.get('status_code', 500))

class LinkedinChatAttendeesView(APIView):
    """Manage attendees of a LinkedIn chat"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request):
        """Get attendees of LinkedIn chat"""
        result = make_lunyamwi_linkedin_request("GET", f"/chat_attendees")
        return Response(result, status=result.get('status_code', 500))

class LinkedInChatAttendeeView(APIView):
    """Add/Remove attendee from LinkedIn chat"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, attendee_id):
        """Get attendee details from LinkedIn chat"""
        result = make_lunyamwi_linkedin_request("GET", f"/chat_attendees/{attendee_id}")
        return Response(result, status=result.get('status_code', 500))

class LinkedInChatAttendeeChatView(APIView):
    """Get LinkedIn chat details for a specific attendee"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, attendee_id):
        """Get attendee chat details"""
        result = make_lunyamwi_linkedin_request("GET", f"/chat_attendees/{attendee_id}/chats")
        return Response(result, status=result.get('status_code', 500))
   
class LinkedInChatAttendeeMessagesView(APIView):
    """Get messages for a specific attendee in a LinkedIn chat"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, sender_id):
        """Get attendee messages"""
        params = {
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'since': request.query_params.get('since'),
            'until': request.query_params.get('until'),
            'search': request.query_params.get('search')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/chat_attendees/{sender_id}/messages", params=params)
        return Response(result, status=result.get('status_code', 500))
    
class LinkedInMessageView(APIView):
    """Single LinkedIn Message management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, message_id):
        """Get specific LinkedIn message"""
        result = make_lunyamwi_linkedin_request("GET", f"/messages/{message_id}")
        return Response(result, status=result.get('status_code', 500))
    
    
class LinkedinRetrieveAttachmentView(APIView):
    """Retrieve LinkedIn message attachment"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, message_id, attachment_id):
        """Get message attachment"""
        result = make_lunyamwi_linkedin_request("GET", f"/messages/{message_id}/attachments/{attachment_id}")
        return Response(result, status=result.get('status_code', 500))


class LinkedInUserInvitationsSentView(APIView):
    """LinkedIn Invitations management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get LinkedIn invitations"""
        params = {
            'account_id': account_id,
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'status': request.query_params.get('status')  # PENDING, ACCEPTED, IGNORED
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/users/invite/sent", params=params)
        return Response(result, status=result.get('status_code', 500))

class LinkedInUserInvitationReceivedView(APIView):
    """LinkedIn Received Invitations management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get received LinkedIn invitations"""
        params = {
            'account_id': account_id,
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'status': request.query_params.get('status')  # PENDING, ACCEPTED, IGNORED
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/users/invite/received", params=params)
        return Response(result, status=result.get('status_code', 500))

    

class LinkedInUserInvitationHandleView(APIView):
    @handle_lunyamwi_linkedin_error
    def post(self, request, invitation_id):
        """Send LinkedIn connection invitation"""
        payload = {
            "provider": "LINKEDIN",
            "action": request.data.get("action", ""),
            "shared_secret": request.data.get("shared_secret", ""),
            "account_id": request.data.get("account_id", "")
        }

        result = make_lunyamwi_linkedin_request("POST", f"/users/invite/received/{invitation_id}", data=payload)
        return Response(result, status=result.get('status_code', 500))

    @handle_lunyamwi_linkedin_error
    def delete(self, request, invitation_id):
        """Delete LinkedIn connection invitation"""
        params = {
            'account_id': request.query_params.get('account_id', '')
        }
        result = make_lunyamwi_linkedin_request("DELETE", f"/users/invite/sent/{invitation_id}", params=params)
        return Response(result, status=result.get('status_code', 500))

class LinkedInUsersSendInvitationView(APIView): 
    """Send LinkedIn Connection Invitation"""
    permission_classes = [AllowAny]

    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id):
        """Send LinkedIn connection invitation"""
        payload = {
            "provider_id": request.data.get("provider_id", ""),
            "account_id": request.data.get("account_id", ""),
            # "user_email": request.data.get("user_email", ""),
            "message": request.data.get("message", "")
        }

        result = make_lunyamwi_linkedin_request("POST", f"/users/invite", data=payload)
        return Response(result, status=result.get('status_code', 500))


class LinkedInUserProfileView(APIView):
    """LinkedIn Profile management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get LinkedIn profile details"""
        params = {
            'account_id': account_id
        }
        result = make_lunyamwi_linkedin_request("GET", f"/users/me", params=params)
        return Response(result, status=result.get('status_code', 500))
    

class LinkedInUserProfileEditView(APIView):
    """Edit LinkedIn Profile"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def patch(self, request, account_id):
        """Edit LinkedIn profile"""
        payload = {
            "account_id": account_id,
            "first_name": request.data.get("first_name", ""),
            "last_name": request.data.get("last_name", ""),
            "headline": request.data.get("headline", ""),
            "location": request.data.get("location", ""),
            "industry": request.data.get("industry", ""),
            "summary": request.data.get("summary", ""),
            "positions": request.data.get("positions", []),  # List of position objects
            "education": request.data.get("education", []),  # List of education objects
            "skills": request.data.get("skills", []),  # List of skills
            "certifications": request.data.get("certifications", []),  # List of certifications
            "languages": request.data.get("languages", []),  # List of languages
            "projects": request.data.get("projects", []),  # List of projects
            "honors": request.data.get("honors", []),  # List of honors/awards
            "courses": request.data.get("courses", [])  # List of courses
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        result = make_lunyamwi_linkedin_request("PATCH", f"/users/me/edit", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInUserRelationsView(APIView):
    """LinkedIn User Relations management"""
    permission_classes = [AllowAny]

    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get LinkedIn user relations"""
        params = {
            'account_id': account_id
        }
        result = make_lunyamwi_linkedin_request("GET", f"/users/relations", params=params)
        return Response(result, status=result.get('status_code', 500))
    

    

class LinkedInUserFollowersView(APIView):
    """LinkedIn User Followers management"""
    permission_classes = [AllowAny]

    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get LinkedIn users following the account"""
        params = {
            'user_id': request.query_params.get('user_id'),
            'account_id': account_id,
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/users/followers", params=params)
        return Response(result, status=result.get('status_code', 500))

class LinkedInUserRetrieveProfileView(APIView):
    """Retrieve LinkedIn profile by user ID or vanity name"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, identifier, account_id):
        """Get LinkedIn profile by user ID or vanity name"""
        params = {
            'account_id': account_id,
            'user_id': identifier if identifier.isdigit() else None,
            'vanity_name': identifier if not identifier.isdigit() else None
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/users/{identifier}", params=params)
        return Response(result, status=result.get('status_code', 500))

class LinkedInUserPostsView(APIView):
    """LinkedIn Posts management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, identifier, account_id):
        """Get LinkedIn posts"""
        params = {
            'account_id': account_id,
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'author_id': request.query_params.get('author_id'),
            'since': request.query_params.get('since'),
            'until': request.query_params.get('until'),
            'include_comments': request.query_params.get('include_comments', 'false'),
            'include_reactions': request.query_params.get('include_reactions', 'false')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/users/{identifier}/posts", params=params)
        return Response(result, status=result.get('status_code', 500))
    

class LinkedInUserCommentsView(APIView):
    """LinkedIn Comments management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, identifier, account_id):
        """Get LinkedIn comments"""
        params = {
            'account_id': account_id,
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'author_id': request.query_params.get('author_id'),
            'since': request.query_params.get('since'),
            'until': request.query_params.get('until'),
            'include_replies': request.query_params.get('include_replies', 'true'),
            'sort_order': request.query_params.get('sort_order', 'CHRONOLOGICAL')  # CHRONOLOGICAL, RELEVANCE
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/users/{identifier}/comments", params=params)
        return Response(result, status=result.get('status_code', 500))
    

class LinkedInUserReactionsView(APIView):
    """LinkedIn Reactions management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, identifier, account_id):
        """Get LinkedIn reactions"""
        params = {
            'account_id': account_id,
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'reaction_type': request.query_params.get('reaction_type'),  # LIKE, LOVE, CELEBRATE, etc.
            'since': request.query_params.get('since'),
            'until': request.query_params.get('until')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/users/{identifier}/reactions", params=params)
        return Response(result, status=result.get('status_code', 500))
    


class LinkedInPostRetrieveView(APIView):
    """Retrieve LinkedIn posts"""
    permission_classes = [AllowAny]

    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, post_id):
        """Get LinkedIn posts"""
        params = {
            'account_id': account_id,
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'author_id': request.query_params.get('author_id'),
            'since': request.query_params.get('since'),
            'until': request.query_params.get('until'),
            'include_comments': request.query_params.get('include_comments', 'false'),
            'include_reactions': request.query_params.get('include_reactions', 'false')
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/posts/{post_id}", params=params)
        return Response(result, status=result.get('status_code', 500))
    

class LinkedInPostView(APIView):
    """Create LinkedIn posts"""
    permission_classes = [AllowAny]

    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id):
        """Create LinkedIn post"""
        payload = {
            "account_id": account_id,
            "text": request.data.get("text"),
            "visibility": request.data.get("visibility", "PUBLIC"),  # PUBLIC, CONNECTIONS, GROUP_MEMBERS
            "attachments": request.data.get("attachments", []),  # List of media IDs
            "tags": request.data.get("tags", []),  # List of user IDs to tag
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/posts", data=payload)
        return Response(result, status=result.get('status_code', 500))


class LinkedInPostCommentsView(APIView):
    """LinkedIn Post comments management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, post_id):
        """Get post comments"""
        params = {
            'account_id': account_id,
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
        }
        params = {k: v for k, v in params.items() if v is not None}

        result = make_lunyamwi_linkedin_request("GET", f"/posts/{post_id}/comments", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id, post_id):
        """Comment on LinkedIn post"""
        payload = {
            "account_id": account_id,
            "text": request.data.get("text"),
            "attachments": request.data.get("attachments", []),
            "mentions": request.data.get("mentions", []),
            "parent_comment_id": request.data.get("parent_comment_id")  # For replies
        }

        result = make_lunyamwi_linkedin_request("POST", f"/posts/{post_id}/comments", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInPostReactionsView(APIView):
    """LinkedIn Post reactions management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, post_id):
        """Get post likes/reactions"""
        params = {
            'account_id': account_id,
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'reaction_type': request.query_params.get('reaction_type')  # LIKE, LOVE, CELEBRATE, etc.
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/posts/{post_id}/reactions", params=params)
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id, post_id):
        """Like/React to LinkedIn post"""
        payload = {
            "account_id": account_id,
            "post_id": post_id,
            "reaction_type": request.data.get("reaction_type", "like")  # like, love, celebrate, support, insightful, funny
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/posts/reaction", data=payload)
        return Response(result, status=result.get('status_code', 500))
    
    


class LinkedInCompanyProfileView(APIView):
    """LinkedIn Company Profile management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, identifier):
        """Get LinkedIn company profile details"""
        params = {
            'account_id': account_id
        }
        result = make_lunyamwi_linkedin_request("GET", f"/linkedin/company/{identifier}", params=params)
        return Response(result, status=result.get('status_code', 500))

class LinkedInInMailBalanceView(APIView):
    """LinkedIn InMail balance retrieval"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get LinkedIn InMail balance"""
        params = {
            'account_id': account_id
        }
        result = make_lunyamwi_linkedin_request("GET", f"/linkedin/inmail_balance", params=params)
        return Response(result, status=result.get('status_code', 500))


class LinkedInSearchParametersView(APIView):
    """LinkedIn Search Parameters management"""
    permission_classes = [AllowAny]

    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get LinkedIn search parameters"""
        params = {
            'account_id': account_id,
            'keywords': request.query_params.get('keywords', 'dev'),
            'type': request.query_params.get('type', 'PEOPLE')  # people, jobs, companies, groups, events
        }
        result = make_lunyamwi_linkedin_request("GET", f"/linkedin/search/parameters", params=params)
        return Response(result, status=result.get('status_code', 500))


class LinkedInSearchView(APIView):
    """LinkedIn Search management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id):
        """Search LinkedIn"""
        payload = {
            "api": "classic",
            "category": request.data.get("category", "people"),
            "keywords": request.data.get("keywords", "alfred")
        }

        result = make_lunyamwi_linkedin_request("POST", f"/linkedin/search?account_id={account_id}", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInJobPostingsView(APIView):
    """LinkedIn Job Postings management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id):
        """Get LinkedIn job postings"""
        params = {
            'account_id': account_id,
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'status': request.query_params.get('status')  # OPEN, CLOSED
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/linkedin/jobs", params=params)
        return Response(result, status=result.get('status_code', 500))


    @handle_lunyamwi_linkedin_error
    def post(self, request, account_id):
        """Create LinkedIn job posting"""
        payload = {
            "account_id": account_id,
            "job_title": { "text": request.data.get("job_title")},
            "location": request.data.get("location"),
            "employment_status": request.data.get("employment_status", "FULL_TIME"),  # FULL_TIME, PART_TIME, CONTRACT, TEMPORARY, INTERN, VOLUNTEER
            "workplace": request.data.get("workplace", "ON_SITE"),  # INTERNSHIP, ENTRY_LEVEL, ASSOCIATE, MID_SENIOR, DIRECTOR, EXECUTIVE
            "company": {"text": request.data.get("company")},
            "description": request.data.get("description"),

        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/linkedin/jobs", data=payload)
        return Response(result, status=result.get('status_code', 500))




class LinkedInJobApplicantsView(APIView):
    """LinkedIn Job Applicants management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request, account_id, job_id):
        """Get applicants for a LinkedIn job posting"""
        params = {
            'account_id': account_id,
            'limit': request.query_params.get('limit', 50),
            'cursor': request.query_params.get('cursor'),
            'status': request.query_params.get('status'),  # NEW, REVIEWED, INTERVIEWING, HIRED, REJECTED
            'service': 'CLASSIC'
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = make_lunyamwi_linkedin_request("GET", f"/linkedin/jobs/{job_id}/applicants", params=params)
        return Response(result, status=result.get('status_code', 500))


    



class LinkedInWebhooksView(APIView):
    """LinkedIn Webhooks management"""
    permission_classes = [AllowAny]
    
    @handle_lunyamwi_linkedin_error
    def get(self, request):
        """Get webhooks"""
        result = make_lunyamwi_linkedin_request("GET", f"/webhooks")
        return Response(result, status=result.get('status_code', 500))
    
    @handle_lunyamwi_linkedin_error
    def post(self, request):
        """Create webhook"""
        payload = {
            "url": request.data.get("url"),
            "events": request.data.get("events", []),  # message_received, post_created, etc.
            "secret": request.data.get("secret")
        }
        
        result = make_lunyamwi_linkedin_request("POST", f"/webhooks", data=payload)
        return Response(result, status=result.get('status_code', 500))

class LinkedInWebhookView(APIView):
    """Single LinkedIn Webhook"""
    permission_classes = [AllowAny]
    
    
    @handle_lunyamwi_linkedin_error
    def delete(self, request, webhook_id):
        """Delete webhook"""
        result = make_lunyamwi_linkedin_request("DELETE", f"/webhooks/{webhook_id}")
        return Response(result, status=result.get('status_code', 500))