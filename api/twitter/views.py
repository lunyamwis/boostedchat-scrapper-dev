import tweepy
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from dotenv import load_dotenv

load_dotenv()

# Twitter API Configuration
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")

# Initialize Tweepy clients
def get_twitter_client_v1():
    """Get Twitter API v1.1 client"""
    auth = tweepy.OAuth1UserHandler(
        TWITTER_API_KEY,
        TWITTER_API_SECRET,
        TWITTER_ACCESS_TOKEN,
        TWITTER_ACCESS_TOKEN_SECRET
    )
    return tweepy.API(auth, wait_on_rate_limit=True)

def get_twitter_client_v2():
    """Get Twitter API v2 client"""
    return tweepy.Client(
        bearer_token=TWITTER_BEARER_TOKEN,
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
        wait_on_rate_limit=True
    )

def handle_twitter_error(func):
    """Decorator to handle Twitter API errors"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except tweepy.TooManyRequests:
            return Response({
                "error": "Rate limit exceeded. Please try again later.",
                "error_code": "rate_limit_exceeded"
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except tweepy.Unauthorized:
            return Response({
                "error": "Unauthorized access. Check your credentials.",
                "error_code": "unauthorized"
            }, status=status.HTTP_401_UNAUTHORIZED)
        except tweepy.Forbidden:
            return Response({
                "error": "Forbidden. You don't have permission to access this resource.",
                "error_code": "forbidden"
            }, status=status.HTTP_403_FORBIDDEN)
        except tweepy.NotFound:
            return Response({
                "error": "Resource not found.",
                "error_code": "not_found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "error": f"An error occurred: {str(e)}",
                "error_code": "internal_error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return wrapper


class TwitterAuthView(APIView):
    """Twitter authentication management"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request):
        """Get authentication URL"""
        auth = tweepy.OAuth1UserHandler(
            TWITTER_API_KEY,
            TWITTER_API_SECRET,
            callback="http://localhost:8000/twitter/auth/callback/"
        )
        try:
            redirect_url = auth.get_authorization_url()
            request.session['request_token'] = auth.request_token
            return Response({
                "auth_url": redirect_url,
                "request_token": auth.request_token
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class TwitterAuthCallbackView(APIView):
    """Handle Twitter auth callback"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def post(self, request):
        """Exchange verifier for access token"""
        oauth_token = request.data.get('oauth_token')
        oauth_verifier = request.data.get('oauth_verifier')
        
        auth = tweepy.OAuth1UserHandler(
            TWITTER_API_KEY,
            TWITTER_API_SECRET
        )
        auth.request_token = request.session.get('request_token', {})
        
        try:
            access_token, access_token_secret = auth.get_access_token(oauth_verifier)
            return Response({
                "access_token": access_token,
                "access_token_secret": access_token_secret
            })
        except Exception as e:
            return Response({"error": str(e)}, status=400)

class TwitterVerifyCredentialsView(APIView):
    """Verify credentials"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request):
        client = get_twitter_client_v1()
        user = client.verify_credentials()
        return Response({
            "id": user.id,
            "screen_name": user.screen_name,
            "name": user.name,
            "followers_count": user.followers_count,
            "friends_count": user.friends_count,
            "statuses_count": user.statuses_count
        })


class TweetView(APIView):
    """Tweet management"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def post(self, request):
        """Create a tweet"""
        tweet_text = request.data.get('text')
        media_ids = request.data.get('media_ids', [])
        reply_to = request.data.get('in_reply_to_status_id')
        
        client = get_twitter_client_v2()
        
        kwargs = {}
        if media_ids:
            kwargs['media_ids'] = media_ids
        if reply_to:
            kwargs['in_reply_to_tweet_id'] = reply_to
        
        response = client.create_tweet(text=tweet_text, **kwargs)
        return Response({
            "id": response.data['id'],
            "text": response.data['text'],
            "created_at": response.data.get('created_at')
        })
    
    @handle_twitter_error
    def get(self, request, tweet_id):
        """Get a tweet"""
        client = get_twitter_client_v2()
        
        expansions = request.query_params.get('expansions', 'author_id,attachments.media_keys')
        tweet_fields = request.query_params.get('tweet_fields', 'created_at,author_id,public_metrics,context_annotations')
        user_fields = request.query_params.get('user_fields', 'username,name,verified,public_metrics')
        media_fields = request.query_params.get('media_fields', 'type,url,duration_ms,height,width')
        
        response = client.get_tweet(
            tweet_id,
            expansions=expansions.split(','),
            tweet_fields=tweet_fields.split(','),
            user_fields=user_fields.split(','),
            media_fields=media_fields.split(',')
        )
        
        tweet_data = response.data._json if hasattr(response.data, '_json') else response.data
        includes = response.includes if hasattr(response, 'includes') else {}
        
        return Response({
            "data": tweet_data,
            "includes": includes
        })
    
    @handle_twitter_error
    def delete(self, request, tweet_id):
        """Delete a tweet"""
        client = get_twitter_client_v2()
        response = client.delete_tweet(tweet_id)
        return Response({
            "deleted": response.data.get('deleted', False)
        })

class TweetRetweetView(APIView):
    """Retweet management"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def post(self, request, tweet_id):
        """Retweet a tweet"""
        client = get_twitter_client_v2()
        response = client.retweet(tweet_id)
        return Response({
            "retweeted": response.data.get('retweeted', False)
        })
    
    @handle_twitter_error
    def delete(self, request, tweet_id):
        """Unretweet a tweet"""
        client = get_twitter_client_v2()
        response = client.unretweet(tweet_id)
        return Response({
            "retweeted": response.data.get('retweeted', True)
        })

class TweetLikeView(APIView):
    """Like management"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def post(self, request, tweet_id):
        """Like a tweet"""
        client = get_twitter_client_v2()
        response = client.like(tweet_id)
        return Response({
            "liked": response.data.get('liked', False)
        })
    
    @handle_twitter_error
    def delete(self, request, tweet_id):
        """Unlike a tweet"""
        client = get_twitter_client_v2()
        response = client.unlike(tweet_id)
        return Response({
            "liked": response.data.get('liked', True)
        })

class TweetBookmarkView(APIView):
    """Bookmark management"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def post(self, request, tweet_id):
        """Bookmark a tweet"""
        client = get_twitter_client_v2()
        response = client.bookmark(tweet_id)
        return Response({
            "bookmarked": response.data.get('bookmarked', False)
        })
    
    @handle_twitter_error
    def delete(self, request, tweet_id):
        """Remove bookmark"""
        client = get_twitter_client_v2()
        response = client.remove_bookmark(tweet_id)
        return Response({
            "bookmarked": response.data.get('bookmarked', True)
        })

class UserBookmarksView(APIView):
    """User bookmarks"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request):
        """Get user's bookmarks"""
        client = get_twitter_client_v2()
        max_results = int(request.query_params.get('max_results', 10))
        pagination_token = request.query_params.get('pagination_token')
        
        kwargs = {'max_results': max_results}
        if pagination_token:
            kwargs['pagination_token'] = pagination_token
        
        response = client.get_bookmarks(**kwargs)
        
        return Response({
            "data": [tweet._json if hasattr(tweet, '_json') else tweet for tweet in response.data] if response.data else [],
            "meta": response.meta if hasattr(response, 'meta') else {}
        })

class TweetSearchView(APIView):
    """Search tweets"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request):
        """Search tweets"""
        query = request.query_params.get('query')
        max_results = int(request.query_params.get('max_results', 10))
        tweet_fields = request.query_params.get('tweet_fields', 'created_at,author_id,public_metrics')
        expansions = request.query_params.get('expansions', 'author_id')
        user_fields = request.query_params.get('user_fields', 'username,name,verified')
        next_token = request.query_params.get('next_token')
        
        client = get_twitter_client_v2()
        
        kwargs = {
            'query': query,
            'max_results': max_results,
            'tweet_fields': tweet_fields.split(','),
            'expansions': expansions.split(','),
            'user_fields': user_fields.split(',')
        }
        
        if next_token:
            kwargs['next_token'] = next_token
        
        response = client.search_recent_tweets(**kwargs)
        
        return Response({
            "data": [tweet._json if hasattr(tweet, '_json') else tweet for tweet in response.data] if response.data else [],
            "includes": response.includes if hasattr(response, 'includes') else {},
            "meta": response.meta if hasattr(response, 'meta') else {}
        })

class TweetSearchAllView(APIView):
    """Search all tweets (Academic Research)"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request):
        """Search all tweets"""
        query = request.query_params.get('query')
        max_results = int(request.query_params.get('max_results', 10))
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        
        client = get_twitter_client_v2()
        
        kwargs = {
            'query': query,
            'max_results': max_results
        }
        
        if start_time:
            kwargs['start_time'] = start_time
        if end_time:
            kwargs['end_time'] = end_time
        
        response = client.search_all_tweets(**kwargs)
        
        return Response({
            "data": [tweet._json if hasattr(tweet, '_json') else tweet for tweet in response.data] if response.data else [],
            "meta": response.meta if hasattr(response, 'meta') else {}
        })

class TweetCountsView(APIView):
    """Get tweet counts"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request):
        """Get tweet counts"""
        query = request.query_params.get('query')
        granularity = request.query_params.get('granularity', 'hour')  # hour, day, minute
        
        client = get_twitter_client_v2()
        
        response = client.get_recent_tweets_count(query, granularity=granularity)
        
        return Response({
            "data": response.data,
            "meta": response.meta if hasattr(response, 'meta') else {}
        })

class TweetQuotesView(APIView):
    """Get tweet quotes"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request, tweet_id):
        """Get quotes for a tweet"""
        client = get_twitter_client_v2()
        max_results = int(request.query_params.get('max_results', 10))
        
        response = client.get_quote_tweets(tweet_id, max_results=max_results)
        
        return Response({
            "data": [tweet._json if hasattr(tweet, '_json') else tweet for tweet in response.data] if response.data else [],
            "meta": response.meta if hasattr(response, 'meta') else {}
        })

class TweetRetweetsView(APIView):
    """Get tweet retweets"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request, tweet_id):
        """Get users who retweeted"""
        client = get_twitter_client_v2()
        max_results = int(request.query_params.get('max_results', 10))
        
        response = client.get_retweeters(tweet_id, max_results=max_results)
        
        return Response({
            "data": [user._json if hasattr(user, '_json') else user for user in response.data] if response.data else [],
            "meta": response.meta if hasattr(response, 'meta') else {}
        })

class TweetLikesView(APIView):
    """Get tweet likes"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request, tweet_id):
        """Get users who liked the tweet"""
        client = get_twitter_client_v2()
        max_results = int(request.query_params.get('max_results', 10))
        
        response = client.get_liking_users(tweet_id, max_results=max_results)
        
        return Response({
            "data": [user._json if hasattr(user, '_json') else user for user in response.data] if response.data else [],
            "meta": response.meta if hasattr(response, 'meta') else {}
        })


class UserView(APIView):
    """User management"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request, user_id=None, username=None):
        """Get user by ID or username"""
        client = get_twitter_client_v2()
        user_fields = request.query_params.get('user_fields', 'created_at,description,public_metrics,verified')
        expansions = request.query_params.get('expansions', 'pinned_tweet_id')
        tweet_fields = request.query_params.get('tweet_fields', 'created_at,public_metrics')
        
        if user_id:
            response = client.get_user(
                id=user_id,
                user_fields=user_fields.split(','),
                expansions=expansions.split(','),
                tweet_fields=tweet_fields.split(',')
            )
        elif username:
            response = client.get_user(
                username=username,
                user_fields=user_fields.split(','),
                expansions=expansions.split(','),
                tweet_fields=tweet_fields.split(',')
            )
        else:
            return Response({"error": "Either user_id or username required"}, status=400)
        
        user_data = response.data._json if hasattr(response.data, '_json') else response.data
        includes = response.includes if hasattr(response, 'includes') else {}
        
        return Response({
            "data": user_data,
            "includes": includes
        })

class UsersView(APIView):
    """Multiple users"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def post(self, request):
        """Get multiple users"""
        user_ids = request.data.get('ids', [])
        usernames = request.data.get('usernames', [])
        user_fields = request.data.get('user_fields', 'created_at,description,public_metrics,verified')
        
        client = get_twitter_client_v2()
        
        if user_ids:
            response = client.get_users(
                ids=user_ids,
                user_fields=user_fields.split(',') if isinstance(user_fields, str) else user_fields
            )
        elif usernames:
            response = client.get_users(
                usernames=usernames,
                user_fields=user_fields.split(',') if isinstance(user_fields, str) else user_fields
            )
        else:
            return Response({"error": "Either ids or usernames required"}, status=400)
        
        return Response({
            "data": [user._json if hasattr(user, '_json') else user for user in response.data] if response.data else []
        })

class UserTweetsView(APIView):
    """User tweets"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request, user_id):
        """Get user's tweets"""
        client = get_twitter_client_v2()
        max_results = int(request.query_params.get('max_results', 10))
        exclude = request.query_params.get('exclude', '')  # replies,retweets
        tweet_fields = request.query_params.get('tweet_fields', 'created_at,public_metrics')
        pagination_token = request.query_params.get('pagination_token')
        
        kwargs = {
            'id': user_id,
            'max_results': max_results,
            'tweet_fields': tweet_fields.split(',')
        }
        
        if exclude:
            kwargs['exclude'] = exclude.split(',')
        if pagination_token:
            kwargs['pagination_token'] = pagination_token
        
        response = client.get_users_tweets(**kwargs)
        
        return Response({
            "data": [tweet._json if hasattr(tweet, '_json') else tweet for tweet in response.data] if response.data else [],
            "meta": response.meta if hasattr(response, 'meta') else {}
        })

class UserMentionsView(APIView):
    """User mentions"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request, user_id):
        """Get mentions for user"""
        client = get_twitter_client_v2()
        max_results = int(request.query_params.get('max_results', 10))
        
        response = client.get_users_mentions(user_id, max_results=max_results)
        
        return Response({
            "data": [tweet._json if hasattr(tweet, '_json') else tweet for tweet in response.data] if response.data else [],
            "meta": response.meta if hasattr(response, 'meta') else {}
        })

class UserLikedTweetsView(APIView):
    """User liked tweets"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request, user_id):
        """Get tweets liked by user"""
        client = get_twitter_client_v2()
        max_results = int(request.query_params.get('max_results', 10))
        
        response = client.get_liked_tweets(user_id, max_results=max_results)
        
        return Response({
            "data": [tweet._json if hasattr(tweet, '_json') else tweet for tweet in response.data] if response.data else [],
            "meta": response.meta if hasattr(response, 'meta') else {}
        })

class UserFollowersView(APIView):
    """User followers"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request, user_id):
        """Get user's followers"""
        client = get_twitter_client_v2()
        max_results = int(request.query_params.get('max_results', 10))
        pagination_token = request.query_params.get('pagination_token')
        
        kwargs = {'id': user_id, 'max_results': max_results}
        if pagination_token:
            kwargs['pagination_token'] = pagination_token
        
        response = client.get_users_followers(**kwargs)
        
        return Response({
            "data": [user._json if hasattr(user, '_json') else user for user in response.data] if response.data else [],
            "meta": response.meta if hasattr(response, 'meta') else {}
        })

class UserFollowingView(APIView):
    """User following"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request, user_id):
        """Get users that this user is following"""
        client = get_twitter_client_v2()
        max_results = int(request.query_params.get('max_results', 10))
        pagination_token = request.query_params.get('pagination_token')
        
        kwargs = {'id': user_id, 'max_results': max_results}
        if pagination_token:
            kwargs['pagination_token'] = pagination_token
        
        response = client.get_users_following(**kwargs)
        
        return Response({
            "data": [user._json if hasattr(user, '_json') else user for user in response.data] if response.data else [],
            "meta": response.meta if hasattr(response, 'meta') else {}
        })
    
    @handle_twitter_error
    def post(self, request, user_id):
        """Follow a user"""
        client = get_twitter_client_v2()
        response = client.follow_user(user_id)
        
        return Response({
            "following": response.data.get('following', False),
            "pending_follow": response.data.get('pending_follow', False)
        })
    
    @handle_twitter_error
    def delete(self, request, user_id):
        """Unfollow a user"""
        client = get_twitter_client_v2()
        response = client.unfollow_user(user_id)
        
        return Response({
            "following": response.data.get('following', True)
        })

class UserBlockView(APIView):
    """User blocking"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def post(self, request, user_id):
        """Block a user"""
        client = get_twitter_client_v2()
        response = client.block(user_id)
        
        return Response({
            "blocking": response.data.get('blocking', False)
        })
    
    @handle_twitter_error
    def delete(self, request, user_id):
        """Unblock a user"""
        client = get_twitter_client_v2()
        response = client.unblock(user_id)
        
        return Response({
            "blocking": response.data.get('blocking', True)
        })

class UserMuteView(APIView):
    """User muting"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def post(self, request, user_id):
        """Mute a user"""
        client = get_twitter_client_v2()
        response = client.mute(user_id)
        
        return Response({
            "muting": response.data.get('muting', False)
        })
    
    @handle_twitter_error
    def delete(self, request, user_id):
        """Unmute a user"""
        client = get_twitter_client_v2()
        response = client.unmute(user_id)
        
        return Response({
            "muting": response.data.get('muting', True)
        })

class UserSearchView(APIView):
    """Search users"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request):
        """Search users"""
        query = request.query_params.get('query')
        count = int(request.query_params.get('count', 20))
        
        client = get_twitter_client_v1()
        users = client.search_users(query, count=count)
        
        return Response({
            "data": [
                {
                    "id": user.id,
                    "screen_name": user.screen_name,
                    "name": user.name,
                    "description": user.description,
                    "followers_count": user.followers_count,
                    "friends_count": user.friends_count,
                    "verified": user.verified,
                    "profile_image_url": user.profile_image_url
                } for user in users
            ]
        })


class MediaUploadView(APIView):
    """Media upload"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def post(self, request):
        """Upload media"""
        client = get_twitter_client_v1()
        
        if 'file' in request.FILES:
            # File upload
            media_file = request.FILES['file']
            media = client.media_upload(filename=media_file.name, file=media_file)
            
            return Response({
                "media_id": media.media_id,
                "media_id_string": media.media_id_string,
                "size": media.size,
                "image": getattr(media, 'image', {}),
                "video": getattr(media, 'video', {})
            })
        elif 'filename' in request.data:
            # File path upload
            filename = request.data['filename']
            media = client.media_upload(filename)
            
            return Response({
                "media_id": media.media_id,
                "media_id_string": media.media_id_string
            })
        else:
            return Response({"error": "No file provided"}, status=400)

class MediaMetadataView(APIView):
    """Media metadata"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def post(self, request, media_id):
        """Create media metadata"""
        client = get_twitter_client_v1()
        alt_text = request.data.get('alt_text')
        
        if not alt_text:
            return Response({"error": "alt_text required"}, status=400)
        
        client.create_media_metadata(media_id, alt_text)
        
        return Response({"success": True, "message": "Metadata created"})


class ListsView(APIView):
    """Lists management"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def post(self, request):
        """Create a list"""
        client = get_twitter_client_v2()
        name = request.data.get('name')
        description = request.data.get('description', '')
        private = request.data.get('private', False)
        
        response = client.create_list(name=name, description=description, private=private)
        
        return Response({
            "id": response.data['id'],
            "name": response.data['name']
        })
    
    @handle_twitter_error
    def get(self, request):
        """Get owned lists"""
        client = get_twitter_client_v2()
        user_id = request.query_params.get('user_id')
        
        if not user_id:
            return Response({"error": "user_id required"}, status=400)
        
        response = client.get_owned_lists(user_id)
        
        return Response({
            "data": [list_item._json if hasattr(list_item, '_json') else list_item for list_item in response.data] if response.data else []
        })

class ListView(APIView):
    """List management"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request, list_id):
        """Get a list"""
        client = get_twitter_client_v2()
        
        response = client.get_list(list_id)
        
        return Response({
            "data": response.data._json if hasattr(response.data, '_json') else response.data
        })
    
    @handle_twitter_error
    def put(self, request, list_id):
        """Update a list"""
        client = get_twitter_client_v2()
        name = request.data.get('name')
        description = request.data.get('description')
        private = request.data.get('private')
        
        response = client.update_list(list_id, name=name, description=description, private=private)
        
        return Response({
            "updated": response.data.get('updated', False)
        })
    
    @handle_twitter_error
    def delete(self, request, list_id):
        """Delete a list"""
        client = get_twitter_client_v2()
        response = client.delete_list(list_id)
        
        return Response({
            "deleted": response.data.get('deleted', False)
        })

class ListTweetsView(APIView):
    """List tweets"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request, list_id):
        """Get tweets from a list"""
        client = get_twitter_client_v2()
        max_results = int(request.query_params.get('max_results', 10))
        
        response = client.get_list_tweets(list_id, max_results=max_results)
        
        return Response({
            "data": [tweet._json if hasattr(tweet, '_json') else tweet for tweet in response.data] if response.data else [],
            "meta": response.meta if hasattr(response, 'meta') else {}
        })

class ListMembersView(APIView):
    """List members"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request, list_id):
        """Get list members"""
        client = get_twitter_client_v2()
        max_results = int(request.query_params.get('max_results', 10))
        
        response = client.get_list_members(list_id, max_results=max_results)
        
        return Response({
            "data": [user._json if hasattr(user, '_json') else user for user in response.data] if response.data else [],
            "meta": response.meta if hasattr(response, 'meta') else {}
        })
    
    @handle_twitter_error
    def post(self, request, list_id):
        """Add member to list"""
        client = get_twitter_client_v2()
        user_id = request.data.get('user_id')
        
        response = client.add_list_member(list_id, user_id)
        
        return Response({
            "is_member": response.data.get('is_member', False)
        })
    
    @handle_twitter_error
    def delete(self, request, list_id):
        """Remove member from list"""
        client = get_twitter_client_v2()
        user_id = request.data.get('user_id')
        
        response = client.remove_list_member(list_id, user_id)
        
        return Response({
            "is_member": response.data.get('is_member', True)
        })

class ListFollowersView(APIView):
    """List followers"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request, list_id):
        """Get list followers"""
        client = get_twitter_client_v2()
        max_results = int(request.query_params.get('max_results', 10))
        
        response = client.get_list_followers(list_id, max_results=max_results)
        
        return Response({
            "data": [user._json if hasattr(user, '_json') else user for user in response.data] if response.data else [],
            "meta": response.meta if hasattr(response, 'meta') else {}
        })
    
    @handle_twitter_error
    def post(self, request, list_id):
        """Follow a list"""
        client = get_twitter_client_v2()
        response = client.follow_list(list_id)
        
        return Response({
            "following": response.data.get('following', False)
        })
    
    @handle_twitter_error
    def delete(self, request, list_id):
        """Unfollow a list"""
        client = get_twitter_client_v2()
        response = client.unfollow_list(list_id)
        
        return Response({
            "following": response.data.get('following', True)
        })

class UserListMembershipsView(APIView):
    """User list memberships"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request, user_id):
        """Get lists user is a member of"""
        client = get_twitter_client_v2()
        max_results = int(request.query_params.get('max_results', 10))
        
        response = client.get_list_memberships(user_id, max_results=max_results)
        
        return Response({
            "data": [list_item._json if hasattr(list_item, '_json') else list_item for list_item in response.data] if response.data else [],
            "meta": response.meta if hasattr(response, 'meta') else {}
        })

class UserFollowedListsView(APIView):
    """User followed lists"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request, user_id):
        """Get lists user follows"""
        client = get_twitter_client_v2()
        max_results = int(request.query_params.get('max_results', 10))
        
        response = client.get_followed_lists(user_id, max_results=max_results)
        
        return Response({
            "data": [list_item._json if hasattr(list_item, '_json') else list_item for list_item in response.data] if response.data else [],
            "meta": response.meta if hasattr(response, 'meta') else {}
        })

class UserPinnedListsView(APIView):
    """User pinned lists"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request, user_id):
        """Get user's pinned lists"""
        client = get_twitter_client_v2()
        
        response = client.get_pinned_lists(user_id)
        
        return Response({
            "data": [list_item._json if hasattr(list_item, '_json') else list_item for list_item in response.data] if response.data else []
        })
    
    @handle_twitter_error
    def post(self, request, list_id):
        """Pin a list"""
        client = get_twitter_client_v2()
        response = client.pin_list(list_id)
        
        return Response({
            "pinned": response.data.get('pinned', False)
        })
    
    @handle_twitter_error
    def delete(self, request, list_id):
        """Unpin a list"""
        client = get_twitter_client_v2()
        response = client.unpin_list(list_id)
        
        return Response({
            "pinned": response.data.get('pinned', True)
        })


class SpacesView(APIView):
    """Spaces management"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def post(self, request):
        """Get multiple spaces"""
        space_ids = request.data.get('ids', [])
        space_fields = request.data.get('space_fields', 'host_ids,created_at,ended_at,participant_count,speaker_ids,started_at,state,title,topic_ids,updated_at')
        user_fields = request.data.get('user_fields', 'name,username')
        expansions = request.data.get('expansions', 'host_ids,speaker_ids')
        
        client = get_twitter_client_v2()
        
        response = client.get_spaces(
            ids=space_ids,
            space_fields=space_fields.split(','),
            user_fields=user_fields.split(','),
            expansions=expansions.split(',')
        )
        
        return Response({
            "data": [space._json if hasattr(space, '_json') else space for space in response.data] if response.data else [],
            "includes": response.includes if hasattr(response, 'includes') else {}
        })

class SpaceView(APIView):
    """Space management"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request, space_id):
        """Get a space"""
        client = get_twitter_client_v2()
        space_fields = request.query_params.get('space_fields', 'host_ids,created_at,ended_at,participant_count,speaker_ids,started_at,state,title,topic_ids,updated_at')
        user_fields = request.query_params.get('user_fields', 'name,username')
        expansions = request.query_params.get('expansions', 'host_ids,speaker_ids')
        
        response = client.get_space(
            id=space_id,
            space_fields=space_fields.split(','),
            user_fields=user_fields.split(','),
            expansions=expansions.split(',')
        )
        
        return Response({
            "data": response.data._json if hasattr(response.data, '_json') else response.data,
            "includes": response.includes if hasattr(response, 'includes') else {}
        })

class SpaceSearchView(APIView):
    """Search Spaces"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request):
        """Search Spaces"""
        query = request.query_params.get('query')
        max_results = int(request.query_params.get('max_results', 10))
        
        client = get_twitter_client_v2()
        
        response = client.search_spaces(query=query, max_results=max_results)
        
        return Response({
            "data": [space._json if hasattr(space, '_json') else space for space in response.data] if response.data else [],
            "meta": response.meta if hasattr(response, 'meta') else {}
        })

class SpaceBuyersView(APIView):
    """Space buyers"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request, space_id):
        """Get Space buyers"""
        client = get_twitter_client_v2()
        
        response = client.get_space_buyers(space_id)
        
        return Response({
            "data": [user._json if hasattr(user, '_json') else user for user in response.data] if response.data else []
        })

class SpaceTweetsView(APIView):
    """Space tweets"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request, space_id):
        """Get Space tweets"""
        client = get_twitter_client_v2()
        
        response = client.get_space_tweets(space_id)
        
        return Response({
            "data": [tweet._json if hasattr(tweet, '_json') else tweet for tweet in response.data] if response.data else []
        })

class DirectMessagesView(APIView):
    """Direct Messages"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def post(self, request):
        """Send direct message"""
        client = get_twitter_client_v1()
        recipient_id = request.data.get('recipient_id')
        text = request.data.get('text')
        
        if not recipient_id or not text:
            return Response({"error": "recipient_id and text required"}, status=400)
        
        message = client.send_direct_message(recipient_id, text)
        
        return Response({
            "id": message.id,
            "text": message.text,
            "created_at": str(message.created_at),
            "sender_id": message.sender_id,
            "recipient_id": message.recipient_id
        })
    
    @handle_twitter_error
    def get(self, request):
        """Get direct messages"""
        client = get_twitter_client_v1()
        count = int(request.query_params.get('count', 20))
        
        messages = client.get_direct_messages(count=count)
        
        return Response({
            "data": [
                {
                    "id": msg.id,
                    "text": msg.text,
                    "created_at": str(msg.created_at),
                    "sender_id": msg.sender_id,
                    "recipient_id": msg.recipient_id
                } for msg in messages
            ]
        })


class TrendsView(APIView):
    """Trends"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request):
        """Get trending topics"""
        client = get_twitter_client_v1()
        woeid = request.query_params.get('woeid', 1)  # 1 = Worldwide
        
        trends = client.get_place_trends(woeid)
        
        return Response({
            "data": trends[0] if trends else {},
            "trends": trends[0]['trends'] if trends and 'trends' in trends[0] else []
        })

class TrendsLocationsView(APIView):
    """Trends locations"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request):
        """Get available trend locations"""
        client = get_twitter_client_v1()
        
        locations = client.available_trends()
        
        return Response({
            "data": locations
        })


class AnalyticsView(APIView):
    """Analytics endpoints"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request):
        """Get account analytics summary"""
        client = get_twitter_client_v1()
        
        # Get user info
        user = client.verify_credentials()
        
        # Get recent tweets for basic analytics
        tweets = client.user_timeline(count=100, include_rts=True, exclude_replies=False)
        
        total_tweets = len(tweets)
        total_retweets = sum(1 for tweet in tweets if hasattr(tweet, 'retweeted_status'))
        total_replies = sum(1 for tweet in tweets if tweet.in_reply_to_status_id)
        total_likes = sum(tweet.favorite_count for tweet in tweets)
        total_tweet_retweets = sum(tweet.retweet_count for tweet in tweets)
        
        return Response({
            "user": {
                "followers_count": user.followers_count,
                "friends_count": user.friends_count,
                "statuses_count": user.statuses_count,
                "favourites_count": user.favourites_count
            },
            "recent_activity": {
                "total_tweets_analyzed": total_tweets,
                "retweets": total_retweets,
                "replies": total_replies,
                "total_likes_received": total_likes,
                "total_retweets_received": total_tweet_retweets,
                "average_likes_per_tweet": total_likes / total_tweets if total_tweets > 0 else 0,
                "average_retweets_per_tweet": total_tweet_retweets / total_tweets if total_tweets > 0 else 0
            }
        })


class BatchOperationsView(APIView):
    """Batch operations"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def post(self, request):
        """Perform batch operations"""
        operation = request.data.get('operation')
        data = request.data.get('data', [])
        
        client = get_twitter_client_v2()
        results = []
        
        if operation == 'follow_users':
            for user_id in data:
                try:
                    response = client.follow_user(user_id)
                    results.append({
                        "user_id": user_id,
                        "success": True,
                        "following": response.data.get('following', False)
                    })
                except Exception as e:
                    results.append({
                        "user_id": user_id,
                        "success": False,
                        "error": str(e)
                    })
        
        elif operation == 'unfollow_users':
            for user_id in data:
                try:
                    response = client.unfollow_user(user_id)
                    results.append({
                        "user_id": user_id,
                        "success": True,
                        "following": response.data.get('following', True)
                    })
                except Exception as e:
                    results.append({
                        "user_id": user_id,
                        "success": False,
                        "error": str(e)
                    })
        
        elif operation == 'like_tweets':
            for tweet_id in data:
                try:
                    response = client.like(tweet_id)
                    results.append({
                        "tweet_id": tweet_id,
                        "success": True,
                        "liked": response.data.get('liked', False)
                    })
                except Exception as e:
                    results.append({
                        "tweet_id": tweet_id,
                        "success": False,
                        "error": str(e)
                    })
        
        elif operation == 'retweet_tweets':
            for tweet_id in data:
                try:
                    response = client.retweet(tweet_id)
                    results.append({
                        "tweet_id": tweet_id,
                        "success": True,
                        "retweeted": response.data.get('retweeted', False)
                    })
                except Exception as e:
                    results.append({
                        "tweet_id": tweet_id,
                        "success": False,
                        "error": str(e)
                    })
        
        else:
            return Response({"error": "Invalid operation"}, status=400)
        
        return Response({
            "operation": operation,
            "results": results,
            "summary": {
                "total": len(data),
                "successful": sum(1 for r in results if r['success']),
                "failed": sum(1 for r in results if not r['success'])
            }
        })


class StreamRulesView(APIView):
    """Stream rules management"""
    permission_classes = [AllowAny]
    
    @handle_twitter_error
    def get(self, request):
        """Get stream rules"""
        client = get_twitter_client_v2()
        
        response = client.get_rules()
        
        return Response({
            "data": response.data if response.data else [],
            "meta": response.meta if hasattr(response, 'meta') else {}
        })
    
    @handle_twitter_error
    def post(self, request):
        """Add stream rules"""
        client = get_twitter_client_v2()
        rules = request.data.get('rules', [])
        
        # Format rules for tweepy
        formatted_rules = []
        for rule in rules:
            if isinstance(rule, str):
                formatted_rules.append(tweepy.StreamRule(rule))
            elif isinstance(rule, dict) and 'value' in rule:
                tag = rule.get('tag')
                formatted_rules.append(tweepy.StreamRule(rule['value'], tag=tag))
        
        response = client.add_rules(formatted_rules)
        
        return Response({
            "data": response.data if response.data else [],
            "meta": response.meta if hasattr(response, 'meta') else {}
        })
    
    @handle_twitter_error
    def delete(self, request):
        """Delete stream rules"""
        client = get_twitter_client_v2()
        rule_ids = request.data.get('rule_ids', [])
        
        response = client.delete_rules(rule_ids)
        
        return Response({
            "meta": response.meta if hasattr(response, 'meta') else {}
        })


class TwitterUtilsView(APIView):
    """Twitter utilities"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get Twitter API status and limits"""
        client = get_twitter_client_v1()
        
        try:
            rate_limit_status = client.rate_limit_status()
            
            return Response({
                "status": "connected",
                "rate_limits": rate_limit_status
            })
        except Exception as e:
            return Response({
                "status": "error",
                "error": str(e)
            }, status=500)

class TwitterConfigView(APIView):
    """Twitter configuration"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get Twitter configuration"""
        client = get_twitter_client_v1()
        
        config = client.configuration()
        
        return Response({
            "data": config._json if hasattr(config, '_json') else config
        })


class TwitterWebhookView(APIView):
    """Twitter webhook handler"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Handle Twitter webhook events"""
        # Process incoming webhook data
        webhook_data = request.data
        
        # Log or process the webhook data as needed
        # You can implement specific logic based on the event type
        
        return Response({"status": "received"})
    
    def get(self, request):
        """Webhook verification"""
        crc_token = request.query_params.get('crc_token')
        
        if crc_token:
            # Implement CRC verification logic
            import hmac
            import hashlib
            import base64
            
            consumer_secret = TWITTER_API_SECRET.encode('utf-8')
            crc_token_bytes = crc_token.encode('utf-8')
            
            hash_digest = hmac.new(consumer_secret, crc_token_bytes, hashlib.sha256).digest()
            response_token = base64.b64encode(hash_digest).decode('utf-8')
            
            return Response({
                "response_token": f"sha256={response_token}"
            })
        
        return Response({"error": "No CRC token provided"}, status=400)