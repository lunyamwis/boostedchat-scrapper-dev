from django.shortcuts import render
import json
import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django_tenants.utils import schema_context
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from api.helpers.models import Client
from .forms import ScrapFacebookGroupForm, SendFirstMessageForm
from .utils import query_gpt
from .models import ChatSession
from .prompts import system_prompt


PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv("TOKEN")
APP_ID = os.getenv('FACEBOOK_APP_ID')
APP_SECRET = os.getenv('FACEBOOK_APP_SECRET')

# Base Graph API URL
GRAPH_API_BASE_URL = "https://graph.facebook.com/v18.0"

# Helper function for Facebook API requests
def make_facebook_request(method: str, endpoint: str, params: Dict = None, data: Dict = None, request = None) -> Dict:
    """Helper function to make requests to Facebook Graph API"""

    url = f"{GRAPH_API_BASE_URL}{endpoint}"
    
    host = request.get_host().split(':')[0]  # hostname without port
    main_domain = 'lunyamwi.org'
    local_main = 'localhost'
    
    access_token = None
    if host == main_domain or host == local_main:
        # Plain main domain or localhost - render home
        auth_header = request.headers.get("Authorization", "")
        access_token = auth_header.replace("Bearer ", "", 1).strip() if auth_header.startswith("Bearer ") else None
    elif host.endswith('.' + main_domain) or host.endswith('.' + local_main):
        tenant = Client.objects.filter(user=request.user).last()
        access_token = tenant.user.token_set.latest('created_at').access_token
    
    if params is None:
        params = {}
    params['access_token'] = access_token
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, params=params)
        elif method.upper() == 'POST':
            response = requests.post(url, params=params, json=data)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, params=params)
        elif method.upper() == 'PUT':
            response = requests.put(url, params=params, json=data)
        else:
            return {"success": False, "error": "Unsupported HTTP method"}
        
        response.raise_for_status()
        return {"success": True, "data": response.json(), "status_code": response.status_code}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e), "status_code": getattr(e.response, 'status_code', 500)}



@api_view(['GET', 'POST'])
def webhook(request):
    """Your existing webhook function"""
    if request.method == 'GET':
        print(request.GET)
        if (request.GET.get("hub.mode") == "subscribe" and
            request.GET.get("hub.verify_token") == VERIFY_TOKEN):
            challenge = request.GET.get("hub.challenge")
            print(challenge)
            return HttpResponse(challenge, status=200)
        else:
            return HttpResponse("Verification failed", status=403)
    elif request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        logging.warning(data)

        if data.get('object') == 'page':            
            for entry in data.get('entry', []):
                for messaging_event in entry.get('messaging', []):
                    if messaging_event.get('message') and messaging_event['message'].get('is_echo'):
                        continue
                    sender_id = messaging_event['sender']['id']

                    if 'message' in messaging_event:
                        message_text = messaging_event['message'].get('text')
                        if message_text:
                            page_id = entry.get('id','')
                            tenant_exists = Client.objects.filter(page_id=page_id)
                            tenant = None
                            if tenant_exists.exists():
                                tenant = tenant_exists.last()

                            # get token
                            token = tenant.user.token_set.latest('created_at').access_token
                            output_message = query_gpt(message_text,sender_id, tenant.schema_name)
                            # get tenant
                            send_message(sender_id, output_message, token)

            return Response({"success":True},status=status.HTTP_200_OK)

def get_user_profile(user_id):
    """Fetch user profile info from Facebook Graph API"""
    url = f"https://graph.facebook.com/v22.0/{user_id}"
    params = {
        'fields': 'first_name,last_name,profile_pic',
        'access_token': PAGE_ACCESS_TOKEN
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return {}

def send_message(recipient_id, message_text, token):
    """Send message to user via Facebook Send API"""
    url = f"https://graph.facebook.com/v22.0/me/messages"
    headers = {'Content-Type': 'application/json'}
    payload = {
        'messaging_type': 'RESPONSE',
        'recipient': {'id': recipient_id},
        'message': {'text': message_text}
    }
    params = {'access_token': token}
    response = requests.post(url, headers=headers, params=params, json=payload)
    if response.status_code != 200:
        print(f"Failed to send message: {response.text}")

# Your existing scraping functions (keep them as they are)

class FacebookAuthURLView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        facebook_auth_url = (
            f"https://www.facebook.com/v12.0/dialog/oauth?"
            f"client_id={os.getenv('FACEBOOK_APP_ID')}"
            f"&redirect_uri={os.getenv('FACEBOOK_REDIRECT_URI')}"
            f"&state=some_random_state"
            f"&scope=email"
        )
        return Response({"auth_url": facebook_auth_url})


class FacebookAuthCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.GET.get('code')
        if not code:
            return Response({"error": "No code provided"}, status=400)

        # Exchange code for access token
        token_url = (
            f"https://graph.facebook.com/v12.0/oauth/access_token?"
            f"client_id={os.getenv('FACEBOOK_APP_ID')}"
            f"&redirect_uri={os.getenv('FACEBOOK_REDIRECT_URI')}"
            f"&client_secret={os.getenv('FACEBOOK_APP_SECRET')}"
            f"&code={code}"
        )
        token_response = requests.get(token_url)
        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            return Response({"error": "Failed to get access token", "details": token_data}, status=400)

        # Get user profile info
        profile_url = (
            f"https://graph.facebook.com/me?"
            f"fields=id,name"
            f"&access_token={access_token}"
        )
        profile_response = requests.get(profile_url)
        profile_data = profile_response.json()

        # Here you would typically create or get the user and issue your own JWT token or session
        return Response({
            "facebook_profile": profile_data,
            "facebook_access_token": access_token
        })

class FacebookUserView(APIView):
    """Facebook User management"""
    permission_classes = [AllowAny]
    
    def get(self, request, user_id="me"):
        """Get user profile"""
        fields = request.query_params.get('fields', 'id,name')
        
        
        result = make_facebook_request(
            request,
            "GET", 
            f"/{user_id}",
            params={'fields': fields},
            request=request

        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookUserAccountsView(APIView):
    """Get user's pages/accounts"""
    permission_classes = [AllowAny]
    
    def get(self, request, user_id="me"):
        """Get user's accounts/pages"""
        
        
        result = make_facebook_request(
            "GET",
            f"/{user_id}/accounts",
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookUserPermissionsView(APIView):
    """Get user permissions"""
    permission_classes = [AllowAny]
    
    def get(self, request, user_id="me"):
        """Get user permissions"""
        
        
        result = make_facebook_request(
            "GET",
            f"/{user_id}/permissions",
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))


class FacebookPageView(APIView):
    """Facebook Page management"""
    permission_classes = [AllowAny]
    
    def get(self, request, page_id):
        """Get page information"""
        fields = request.query_params.get('fields', 'id,name,about,category,fan_count,followers_count,website,phone,location')
        
        
        result = make_facebook_request(
            "GET",
            f"/{page_id}",
            params={'fields': fields},
            request=request
        )
        # result.update({"requested_path": request.path, "schema": request.tenant.schema_name})
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, page_id):
        """Update page information"""
        
        
        result = make_facebook_request(
            "POST",
            f"/{page_id}",
            data=request.data,
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookPageInsightsView(APIView):
    """Page insights/analytics"""
    permission_classes = [AllowAny]
    
    def get(self, request, page_id):
        """Get page insights"""
        metric = request.query_params.get('metric', 'page_fans')
        period = request.query_params.get('period', 'day')
        since = request.query_params.get('since')
        until = request.query_params.get('until')
        
        
        params = {'metric': metric, 'period': period}
        if since:
            params['since'] = since
        if until:
            params['until'] = until
        
        result = make_facebook_request(
            "GET",
            f"/{page_id}/insights",
            params=params,
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookPageConversationsView(APIView):
    """Page conversations"""
    permission_classes = [AllowAny]
    
    def get(self, request, page_id):
        """Get page conversations"""
        
        limit = request.query_params.get('limit', 25)
        
        result = make_facebook_request(
            "GET",
            f"/{page_id}/conversations",
            params={'limit': limit},
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))


class FacebookPostsView(APIView):
    """Facebook Posts management"""
    permission_classes = [AllowAny]
    
    def get(self, request, page_id):
        """Get page posts"""
        fields = request.query_params.get('fields', 'id,message,created_time,likes.summary(true),comments.summary(true),shares')
        limit = request.query_params.get('limit', 25)
        
        
        result = make_facebook_request(
            "GET",
            f"/{page_id}/posts",
            params={'fields': fields, 'limit': limit},
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, page_id):
        """Create a post"""
        
        
        result = make_facebook_request(
            "POST",
            f"/{page_id}/feed",
            data=request.data,
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookPostView(APIView):
    """Single post management"""
    permission_classes = [AllowAny]
    
    def get(self, request, post_id):
        """Get specific post"""
        fields = request.query_params.get('fields', 'id,message,created_time,likes.summary(true),comments.summary(true),shares')
        
        
        result = make_facebook_request(
            "GET",
            f"/{post_id}",
            params={'fields': fields},
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, post_id):
        """Update post"""
        
        
        result = make_facebook_request(
            "POST",
            f"/{post_id}",
            data=request.data,
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, post_id):
        """Delete post"""
        
        
        result = make_facebook_request(
            "DELETE",
            f"/{post_id}",
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookPostLikesView(APIView):
    """Post likes management"""
    permission_classes = [AllowAny]
    
    def get(self, request, post_id):
        """Get post likes"""
        
        limit = request.query_params.get('limit', 25)
        
        result = make_facebook_request(
            "GET",
            f"/{post_id}/likes",
            params={'limit': limit},
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, post_id):
        """Like a post"""
        
        
        result = make_facebook_request(
            "POST",
            f"/{post_id}/likes",
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, post_id):
        """Unlike a post"""
        
        
        result = make_facebook_request(
            "DELETE",
            f"/{post_id}/likes",
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookPostCommentsView(APIView):
    """Post comments management"""
    permission_classes = [AllowAny]
    
    def get(self, request, post_id):
        """Get post comments"""
        
        limit = request.query_params.get('limit', 25)
        order = request.query_params.get('order', 'chronological')
        
        result = make_facebook_request(
            "GET",
            f"/{post_id}/comments",
            params={'limit': limit, 'order': order},
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, post_id):
        """Comment on post"""
        
        
        result = make_facebook_request(
            "POST",
            f"/{post_id}/comments",
            data=request.data,
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookCommentView(APIView):
    """Comment management"""
    permission_classes = [AllowAny]
    
    def get(self, request, comment_id):
        """Get comment"""
        fields = request.query_params.get('fields', 'id,message,created_time,from,likes.summary(true)')
        
        
        result = make_facebook_request(
            "GET",
            f"/{comment_id}",
            params={'fields': fields},
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, comment_id):
        """Update comment"""
        
        
        result = make_facebook_request(
            "POST",
            f"/{comment_id}",
            data=request.data,
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, comment_id):
        """Delete comment"""
        
        
        result = make_facebook_request(
            "DELETE",
            f"/{comment_id}",
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookMessagesView(APIView):
    """Messenger Platform - Send Messages"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Send message via Messenger Platform"""
        
        
        # Enhanced message sending with various message types
        payload = {
            'messaging_type': request.data.get('messaging_type', 'RESPONSE'),
            'recipient': request.data.get('recipient'),
            'message': request.data.get('message')
        }
        
        # Add optional fields
        if 'sender_action' in request.data:
            payload['sender_action'] = request.data['sender_action']
        if 'notification_type' in request.data:
            payload['notification_type'] = request.data['notification_type']
        if 'tag' in request.data:
            payload['tag'] = request.data['tag']
        
        result = make_facebook_request(
            "POST",
            "/me/messages",
            data=payload,
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookMessengerProfileView(APIView):
    """Messenger Profile API"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get Messenger Profile"""
        
        fields = request.query_params.get('fields', 'get_started,greeting,persistent_menu')
        
        result = make_facebook_request(
            "GET",
            "/me/messenger_profile",
            params={'fields': fields},
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request):
        """Set Messenger Profile"""
        
        
        result = make_facebook_request(
            "POST",
            "/me/messenger_profile",
            data=request.data,
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request):
        """Delete Messenger Profile fields"""
        
        
        result = make_facebook_request(
            "DELETE",
            "/me/messenger_profile",
            data=request.data,
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))


class FacebookPhotosView(APIView):
    """Photos management"""
    permission_classes = [AllowAny]
    
    def get(self, request, page_id):
        """Get page photos"""
        
        limit = request.query_params.get('limit', 25)
        
        result = make_facebook_request(
            "GET",
            f"/{page_id}/photos",
            params={'limit': limit},
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, page_id):
        """Upload photo"""
        
        
        result = make_facebook_request(
            "POST",
            f"/{page_id}/photos",
            data=request.data,
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookVideosView(APIView):
    """Videos management"""
    permission_classes = [AllowAny]
    
    def get(self, request, page_id):
        """Get page videos"""
        
        limit = request.query_params.get('limit', 25)
        
        result = make_facebook_request(
            "GET",
            f"/{page_id}/videos",
            params={'limit': limit},
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, page_id):
        """Upload video"""
        
        
        result = make_facebook_request(
            "POST",
            f"/{page_id}/videos",
            data=request.data,
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookAlbumsView(APIView):
    """Albums management"""
    permission_classes = [AllowAny]
    
    def get(self, request, page_id):
        """Get page albums"""
        
        limit = request.query_params.get('limit', 25)
        
        result = make_facebook_request(
            "GET",
            f"/{page_id}/albums",
            params={'limit': limit},
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, page_id):
        """Create album"""
        
        
        result = make_facebook_request(
            "POST",
            f"/{page_id}/albums",
            data=request.data,
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookEventsView(APIView):
    """Events management"""
    permission_classes = [AllowAny]
    
    def get(self, request, page_id):
        """Get page events"""
        
        fields = request.query_params.get('fields', 'id,name,description,start_time,end_time,place')
        
        result = make_facebook_request(
            "GET",
            f"/{page_id}/events",
            params={'fields': fields},
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, page_id):
        """Create event"""
        
        
        result = make_facebook_request(
            "POST",
            f"/{page_id}/events",
            data=request.data,
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookEventView(APIView):
    """Single event management"""
    permission_classes = [AllowAny]
    
    def get(self, request, event_id):
        """Get event details"""
        
        fields = request.query_params.get('fields', 'id,name,description,start_time,end_time,place,attending_count')
        
        result = make_facebook_request(
            "GET",
            f"/{event_id}",
            params={'fields': fields},
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookGroupView(APIView):
    """Single group management"""
    permission_classes = [AllowAny]
    
    def get(self, request, group_id):
        """Get group details"""
        
        fields = request.query_params.get('fields', 'id,name,description,privacy,member_count')
        
        result = make_facebook_request(
            "GET",
            f"/{group_id}",
            params={'fields': fields},
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookGroupFeedView(APIView):
    """Group feed"""
    permission_classes = [AllowAny]
    
    def get(self, request, group_id):
        """Get group feed"""
        
        limit = request.query_params.get('limit', 25)
        
        result = make_facebook_request(
            "GET",
            f"/{group_id}/feed",
            params={'limit': limit},
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, group_id):
        """Post to group"""
        
        
        result = make_facebook_request(
            "POST",
            f"/{group_id}/feed",
            data=request.data,
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookWebhookSubscriptionsView(APIView):
    """Webhook subscriptions management"""
    permission_classes = [AllowAny]
    
    def get(self, request, page_id):
        """Get webhook subscriptions"""
        
        
        result = make_facebook_request(
            "GET",
            f"/{page_id}/subscriptions",
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, page_id):
        """Subscribe to webhooks"""
        
        
        result = make_facebook_request(
            "POST",
            f"/{page_id}/subscriptions",
            data=request.data,
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookLeadGenFormsView(APIView):
    """Lead generation forms"""
    permission_classes = [AllowAny]
    
    def get(self, request, page_id):
        """Get lead forms"""
        
        
        result = make_facebook_request(
            "GET",
            f"/{page_id}/leadgen_forms",
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookLeadsView(APIView):
    """Leads management"""
    permission_classes = [AllowAny]
    
    def get(self, request, form_id):
        """Get leads from form"""
        
        
        result = make_facebook_request(
            "GET",
            f"/{form_id}/leads",
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookInstagramAccountView(APIView):
    """Instagram account management"""
    permission_classes = [AllowAny]
    
    def get(self, request, page_id):
        """Get connected Instagram account"""
        
        
        result = make_facebook_request(
            "GET",
            f"/{page_id}",
            params={'fields': 'instagram_business_account'},
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookInstagramMediaView(APIView):
    """Instagram media management"""
    permission_classes = [AllowAny]
    
    def get(self, request, instagram_account_id):
        """Get Instagram media"""
        
        fields = request.query_params.get('fields', 'id,caption,media_type,media_url,timestamp')
        
        result = make_facebook_request(
            "GET",
            f"/{instagram_account_id}/media",
            params={'fields': fields},
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, instagram_account_id):
        """Create Instagram media"""
        
        
        result = make_facebook_request(
            "POST",
            f"/{instagram_account_id}/media",
            data=request.data,
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookDebugTokenView(APIView):
    """Debug access token"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Debug access token"""
        input_token = request.query_params.get('input_token', PAGE_ACCESS_TOKEN)
        access_token = f"{APP_ID}|{APP_SECRET}"
        
        result = make_facebook_request(
            "GET",
            "/debug_token",
            params={'input_token': input_token},
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))


class FacebookBatchRequestView(APIView):
    """Batch requests"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Execute batch requests"""
        
        
        batch_requests = request.data.get('batch', [])
        
        result = make_facebook_request(
            "POST",
            "/",
            data={'batch': json.dumps(batch_requests)},
            request=request
        )
        
        return Response(result, status=result.get('status_code', 500))