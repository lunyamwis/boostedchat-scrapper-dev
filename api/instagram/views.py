import yaml
import ast
import os
import json
import uuid
import logging
import requests
import pandas as pd
import subprocess
import docker
# Custom Field API Views
# Create your views here.
import csv
import io
import time
import requests
import random
import pytz
from requests.auth import HTTPBasicAuth
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from django.conf import settings
from django.utils import timezone
from django.contrib import messages
from .tasks import scrap_followers,scrap_info,scrap_users,insert_and_enrich,scrap_mbo,scrap_media,load_info_to_database,scrap_hash_tag
from api.helpers.dag_generator import generate_dag
from api.helpers.dag_file_handler import push_file,push_file_gcp
from api.helpers.date_helper import datetime_to_cron_expression
from api.scout.models import Scout
from boostedchatScrapper.spiders.helpers.thecut_scrapper import scrap_the_cut
from boostedchatScrapper.spiders.helpers.instagram_helper import fetch_pending_inbox,approve_inbox_requests,send_direct_answer
from django.db.models import Q
from django.utils.timezone import make_aware, now

from .models import InstagramUser
from django_tenants.utils import schema_context

from rest_framework import viewsets
from boostedchatScrapper.models import ScrappedData
from instagrapi import Client


from .models import Score, QualificationAlgorithm, Scheduler, AirflowCreds, InstagramUser, LeadSource,DagModel,SimpleHttpOperatorModel,HttpOperatorConnectionModel, WorkflowModel, Endpoint,CustomField,CustomFieldValue,Media,Scout,Account, Comment, HashTag, Photo, Reel, Story, Thread, Video, Message, OutSourced,OutreachTime,AccountsClosed,Like,Comment,UnwantedAccount,StatusCheck

from django.shortcuts import render, redirect, get_object_or_404
from .forms import WorkflowModelForm
from .utils import assign_salesrep, generate_dag_script, initialize_hikerapi_client


# 6th
from django.contrib import messages
from django.views.generic import ListView,DeleteView,DetailView,View
from django.views.generic.edit import (
    CreateView, UpdateView
)

from .forms import (
    WorkflowModelForm, SimpleHttpOperatorFormSet, DagFormSet,HttpOperatorConnectionForm,WorkflowRunnerForm,EndpointForm,CustomFieldForm,CustomFieldValueForm
)
from django.urls import reverse_lazy
from boostedchatScrapper.spiders.helpers.instagram_login_helper import login_user

# views.py
from .serializers import (
    ScoreSerializer, 
    InstagramLeadSerializer,  
    QualificationAlgorithmSerializer, 
    SchedulerSerializer, 
    LeadSourceSerializer, 
    SimpleHttpOperatorModelSerializer, WorkflowModelSerializer,
    MediaSerializer,
    CustomFieldSerializer,
    CustomFieldValueSerializer,
    EndpointSerializer,
    HttpOperatorConnectionModelSerializer,
    WorkflowModelSerializer,
    AccountSerializer,
    OutSourcedSerializer,
    AddContentSerializer,
    HashTagSerializer,
    PhotoSerializer,
    ReelSerializer,
    SingleThreadSerializer,
    StorySerializer,
    ThreadSerializer,
    ThreadMessageSerializer,
    UploadSerializer,
    VideoSerializer,
    MessageSerializer,
    SendManualMessageSerializer,
    GetAccountSerializer,
    GetSingleAccountSerializer,
    ScheduleOutreachSerializer,
    LikeSerializer,
    CommentSerializer,
)

from urllib.parse import urlparse
from auditlog.models import LogEntry
from celery.result import AsyncResult
from datetime import datetime, timedelta, time, timezone as timezone2
from instagrapi.exceptions import UserNotFound
from rest_framework.views import APIView
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from lunyamwi.model_setup import setup_agent, setup_agent_workflow
from django.conf import settings
from django_celery_beat.models import PeriodicTask
from django.db.models import F,Value, Subquery, OuterRef
from django.db.models.functions import Coalesce
from django.utils.dateparse import parse_datetime


from api.helpers.push_id import PushID
from api.dialogflow.helpers.get_prompt_responses import get_gpt_response

from django_celery_beat.models import CrontabSchedule, PeriodicTask
from api.dialogflow.helpers.intents import detect_intent
from boostedchatScrapper.spiders.helpers.instagram_login_helper import login_user
from api.sales_rep.models import SalesRep

from .utils import generate_time_slots

from .tasks import send_first_compliment,generate_response_automatic,reschedule, run_scheduler, delete_accounts,prequalify_task
from api.instagram.helpers.init_db import init_db


from django.db.models import Count, Case, When, IntegerField





class GetCommentLikers(APIView):
    def post(self, request, *args, **kwargs):
        # Get the media ID from the request data
        media_id = request.data.get('media_id')
        if not media_id:
            return Response({"error": "Media ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Initialize the HikerAPI client
        cl = initialize_hikerapi_client()
        try:
            # Fetch the likers of the media
            likers = cl.comment_likers_chunk_gql(media_id)
            likers_list = []
            for liker in likers:
                liker_data = {
                    "username": liker.username,
                    "full_name": liker.full_name,
                    "profile_pic_url": liker.profile_pic_url,
                    "is_verified": liker.is_verified
                }
                try:
                    InstagramUser.objects.create(
                        username=liker.username,
                        full_name=liker.full_name,
                        profile_pic_url=liker.profile_pic_url,
                        is_verified=liker.is_verified
                    )
                except Exception as e:
                    # Handle the case where the user already exists
                    print(f"User {liker.username} already exists in the database.")
                # Add the liker data to the list
                likers_list.append(liker_data)
            return Response({"likers": likers_list}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class GetComments(APIView):
    def post(self, request, *args, **kwargs):
        # Get the media ID from the request data
        media_id = request.data.get('media_id')
        if not media_id:
            return Response({"error": "Media ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Initialize the HikerAPI client
        cl = initialize_hikerapi_client()
        try:
            # Fetch the comments of the media
            comments = cl.comments_chunk_gql(media_id)
            comments_list = []
            for comment in comments:
                comment_data = {
                    "id": comment.id,
                    "text": comment.text,
                    "user": comment.user.username,
                    "created_at": comment.created_at,
                    "likers": [liker.username for liker in cl.comment_likers_chunk_gql(comment.id)]
                }
                try:
                    InstagramUser.objects.create(
                        username=comment.user.username,
                        full_name=comment.user.full_name,
                        profile_pic_url=comment.user.profile_pic_url,
                        is_verified=comment.user.is_verified
                    )
                except Exception as e:
                    # Handle the case where the user already exists
                    print(f"User {comment.user.username} already exists in the database.")
                comments_list.append(comment_data)
            return Response({"comments": comments_list}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class GetCommentsThreadedChunk(APIView):
    def post(self, request, *args, **kwargs):
        # Get the media ID from the request data
        media_id = request.data.get('media_id')
        if not media_id:
            return Response({"error": "Media ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Initialize the HikerAPI client
        cl = initialize_hikerapi_client()
        try:
            # Fetch the comments of the media
            comments = cl.comments_threaded_chunk_gql(media_id)
            comments_list = []
            for comment in comments:
                comment_data = {
                    "id": comment.id,
                    "text": comment.text,
                    "user": comment.user.username,
                    "created_at": comment.created_at,
                    "likers": [liker.username for liker in cl.comment_likers_chunk_gql(comment.id)]
                }
                try:
                    InstagramUser.objects.create(
                        username=comment.user.username,
                        full_name=comment.user.full_name,
                        profile_pic_url=comment.user.profile_pic_url,
                        is_verified=comment.user.is_verified
                    )
                except Exception as e:
                    # Handle the case where the user already exists
                    print(f"User {comment.user.username} already exists in the database.")
                comments_list.append(comment_data)
            return Response({"comments": comments_list}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FbSearchAccounts(APIView):
    def post(self, request, *args, **kwargs):
        query = request.data.get('query')
        if not query:
            return Response({"error": "Query is required."}, status=status.HTTP_400_BAD_REQUEST)
        # Initialize the HikerAPI client
        cl = initialize_hikerapi_client()
        try:
            # Search for accounts
            accounts = cl.fb_search_accounts(query)
            accounts_list = []
            for account in accounts:
                account_data = {
                    "username": account.username,
                    "full_name": account.full_name,
                    "profile_pic_url": account.profile_pic_url,
                    "is_verified": account.is_verified
                }
                try:
                    InstagramUser.objects.create(
                        username=account.username,
                        full_name=account.full_name,
                        profile_pic_url=account.profile_pic_url,
                        is_verified=account.is_verified
                    )
                except Exception as e:
                    # Handle the case where the user already exists
                    print(f"User {account.username} already exists in the database.")
                accounts_list.append(account_data)
            return Response({"accounts": accounts_list}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class FbSearchPlaces(APIView):
    def post(self, request, *args, **kwargs):
        query = request.data.get('query')
        if not query:
            return Response({"error": "Query is required."}, status=status.HTTP_400_BAD_REQUEST)
        # Initialize the HikerAPI client
        cl = initialize_hikerapi_client()
        try:
            # Search for places
            places = cl.fb_search_places(query)
            places_list = []
            for place in places:
                place_data = {
                    "name": place.name,
                    "location": place.location,
                    "category": place.category,
                    "latitude": place.latitude,
                    "longitude": place.longitude
                }
                places_list.append(place_data)
            return Response({"places": places_list}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class FbSearchReels(APIView):
    def post(self, request, *args, **kwargs):
        query = request.data.get('query')
        if not query:
            return Response({"error": "Query is required."}, status=status.HTTP_400_BAD_REQUEST)
        # Initialize the HikerAPI client
        cl = initialize_hikerapi_client()
        try:
            # Search for reels
            reels = cl.fb_search_reels(query)
            reels_list = []
            for reel in reels:
                reel_data = {
                    "username": reel.username,
                    "media_id": reel.media_id,
                    "created_at": reel.created_at,
                    "is_verified": reel.is_verified
                }
                reels_list.append(reel_data)
            return Response({"reels": reels_list}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class FbSearchHashtags(APIView):
    def post(self, request, *args, **kwargs):
        query = request.data.get('query')
        if not query:
            return Response({"error": "Query is required."}, status=status.HTTP_400_BAD_REQUEST)
        # Initialize the HikerAPI client
        cl = initialize_hikerapi_client()
        try:
            # Search for hashtags
            hashtags = cl.fb_search_hashtags(query)
            hashtags_list = []
            for hashtag in hashtags:
                hashtag_data = {
                    "name": hashtag.name,
                    "media_count": hashtag.media_count
                }
                hashtags_list.append(hashtag_data)
            return Response({"hashtags": hashtags_list}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FbSearchTopsearch(APIView):
    def post(self, request, *args, **kwargs):
        query = request.data.get('query')
        if not query:
            return Response({"error": "Query is required."}, status=status.HTTP_400_BAD_REQUEST)
        # Initialize the HikerAPI client
        cl = initialize_hikerapi_client()
        try:
            # Search for top search results
            top_search_results = cl.fb_search_topsearch(query)
            top_search_list = []
            for result in top_search_results:
                result_data = {
                    "username": result.username,
                    "full_name": result.full_name,
                    "profile_pic_url": result.profile_pic_url,
                    "is_verified": result.is_verified
                }
                try:
                    InstagramUser.objects.create(
                        username=result.username,
                        full_name=result.full_name,
                        profile_pic_url=result.profile_pic_url,
                        is_verified=result.is_verified
                    )
                except Exception as e:
                    # Handle the case where the user already exists
                    print(f"User {result.username} already exists in the database.")
                top_search_list.append(result_data)
            return Response({"top_search_results": top_search_list}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class GetHashTagByName(APIView):
    def post(self, request, *args, **kwargs):
        # Get the hashtag name from the request data
        hashtag_name = request.data.get('hashtag_name')
        if not hashtag_name:
            return Response({"error": "Hashtag name is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Initialize the HikerAPI client
        cl = initialize_hikerapi_client()
        try:
            # Fetch the hashtag details
            hashtag = cl.hashtag_by_name_v1(hashtag_name)
            hashtag_data = {
                "name": hashtag.name,
                "media_count": hashtag.media_count,
                "profile_pic_url": hashtag.profile_pic_url,
                "is_verified": hashtag.is_verified
            }
            # try:
            #     InstagramUser.objects.create(
            #         username=hashtag.name,
            #         full_name=hashtag.name,
            #         profile_pic_url=hashtag.profile_pic_url,
            #         is_verified=hashtag.is_verified
            #     )
            # except Exception as e:
            #     # Handle the case where the user already exists
            #     print(f"User {hashtag.name} already exists in the database.")
            return Response({"hashtag": hashtag_data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetMediaById(APIView):
    def post(self, request, *args, **kwargs):
        # Get the media ID from the request data
        media_id = request.data.get('media_id')
        if not media_id:
            return Response({"error": "Media ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Initialize the HikerAPI client
        cl = initialize_hikerapi_client()
        try:
            # Fetch the media details
            media = cl.media_by_id_v1(media_id)
            media_data = {
                "id": media.id,
                "caption": media.caption,
                "user": media.user.username,
                "created_at": media.created_at,
                "is_verified": media.is_verified
            }
            return Response({"media": media_data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class GetMediaLikers(APIView):
    def post(self, request, *args, **kwargs):
        # Get the media ID from the request data
        media_links = request.data.get('media_links')
        if not media_links:
            return Response({"error": "Media Links is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Initialize the HikerAPI client
        cl = initialize_hikerapi_client()
        likers_list = []
        for link in media_links:
            try:
                # Fetch the likers of the media
                media_id = cl.media_pk_from_url_v1(link)
                likers = cl.media_likers_v2(media_id)
                for liker in likers['users']:
                    liker_data = {
                        "username": liker['username'],
                        "full_name": liker['full_name'],
                        "profile_pic_url": liker['profile_pic_url'],
                        "is_verified": liker['is_verified']
                    }
                    try:
                        InstagramUser.objects.create(
                            username=liker['username'],
                            info = cl.user_by_username_v2(liker['username'])
                        )
                    except Exception as e:
                        # Handle the case where the user already exists
                        print(f"User {liker.username} already exists in the database.")
                    
                    try:
                        account = Account.objects.create(
                            igname=liker['username'],
                            relevant_information=cl.user_by_username_v2(liker['username'])
                        )
                        OutSourced.objects.create(
                            results = cl.user_by_username_v2(liker['username']),
                            account = account
                        )
                        logging.info(f"Account {liker['username']} created successfully.")
                    except Exception as e:
                        # Handle the case where the user already exists
                        print(f"User {liker.username} already exists in the database.")
                    # Add the liker data to the list
                    likers_list.append(liker_data)
                
            except Exception as e:
                logging.warning(f"error: {str(e)}")
        return Response({"likers": likers_list}, status=status.HTTP_200_OK)
    


class GetMediaCommenters(APIView):
    def post(self, request, *args, **kwargs):
        # Get the media ID from the request data
        media_links = request.data.get('media_links')
        if not media_links:
            return Response({"error": "Media Links is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Initialize the HikerAPI client
        cl = initialize_hikerapi_client()
        commenters_list = []
        for link in media_links:
            try:
                # Fetch the likers of the media
                media_id = cl.media_pk_from_url_v1(link)
                commenters = cl.media_commenters_v2(media_id)
                for commenter in commenters['response']['comments']:
                    commenter_data = {
                        "username": commenter['user']['username'],
                        "full_name": commenter['user']['full_name'],
                        "profile_pic_url": commenter['user']['profile_pic_url'],
                        "is_verified": commenter['user']['is_verified']
                    }
                    try:
                        InstagramUser.objects.create(
                            username=commenter['user']['username'],
                            info = cl.user_by_username_v2(commenter['user']['username'])
                        )
                    except Exception as e:
                        # Handle the case where the user already exists
                        print(f"User already exists in the database: {e}")
                    
                    try:
                        account = Account.objects.create(
                            igname=commenter['username'],
                            relevant_information=cl.user_by_username_v2(commenter['user']['username'])
                        )
                        OutSourced.objects.create(
                            results = cl.user_by_username_v2(commenter['user']['username']),
                            account = account
                        )
                        logging.info(f"Account {commenter['user']['username']} created successfully.")
                    except Exception as e:
                        # Handle the case where the user already exists
                        print(f"User already exists in the database: {e}")
                    # Add the liker data to the list
                    commenters_list.append(commenter_data)
                
            except Exception as e:
                logging.warning(f"error: {str(e)}")
        return Response({"commenters": commenters_list}, status=status.HTTP_200_OK)
    


class GetUserMediaId(APIView):
    def post(self, request, *args, **kwargs):
        # Get the media ID from the request data
        username = request.data.get('username')
        if not username:
            return Response({"error": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Initialize the HikerAPI client
        cl = initialize_hikerapi_client()
        media_id = None
        try:
            medias = cl.user_medias_v2(user_id=cl.user_by_username_v1(username=username).get("pk"))
            media_id = medias['response']['items'][0]['id']
        except Exception as e:
            print(f"Error fetching media ID: {e}")

        return Response({"media_id": media_id}, status=status.HTTP_200_OK)

class PaginationClass(PageNumberPagination):
    page_size = 20  # Set the number of items per page
    page_size_query_param = 'page_size'
    max_page_size = 100

class OutSourcedViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    with schema_context(os.getenv('SCHEMA_NAME')):queryset = OutSourced.objects.filter(account__isnull=False)
    serializer_class = OutSourcedSerializer
    # import pdb;pdb.set_trace()
    pagination_class = PaginationClass


class LikeViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    with schema_context(os.getenv('SCHEMA_NAME')):queryset = Like.objects.filter(account__isnull=False)
    serializer_class = LikeSerializer
    pagination_class = PaginationClass
    
    @schema_context(os.getenv('SCHEMA_NAME'))
    def create(self, request):   
        title = request.data.get('title')
        message = request.data.get('message')
        media_id =  request.data.get('media_id')
        collapse_key = request.data.get('collapse_key')
        optional_avatar_url = request.data.get('optional_avatar_url') 
        push_id =  request.data.get('push_id')
        push_category = request.data.get('push_category')
        intended_recipient_user_id = request.data.get('intended_recipient_user_id')
        source_user_id =  request.data.get('source_user_id')
        
        # Get or create account based on title
        try:
            account, created = Account.objects.get_or_create(igname=title)
        except Exception as error:
            print(error)

        # Create a new comment instance
        like_data = {
            'account': account.id,  # Use account ID for ForeignKey
            'message': message,
            'media_id': media_id,
            'collapseKey': collapse_key,
            'optionalAvatarUrl': optional_avatar_url,
            'pushId': push_id,
            'pushCategory': push_category,
            'intendedRecipientUserId': intended_recipient_user_id,
            'sourceUserId': source_user_id
        }

        # Initialize the serializer with the prepared data
        serializer = LikeSerializer(data=like_data)


        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @schema_context(os.getenv('SCHEMA_NAME'))
    def list(self, request, pk=None):
        paginator = self.pagination_class()
        queryset = Like.objects.all()
        result_page = paginator.paginate_queryset(queryset, request)  # Apply pagination
        likes = []
        
        for like in result_page:
            like_ = {
                "id": like.id,
                "deleted_at": like.deleted_at,
                "message": like.message,
                "media_id": like.media_id,
                "collapseKey": like.collapseKey,
                "optionalAvatarUrl": like.optionalAvatarUrl,
                "pushId": like.pushId,
                "pushCategory": like.pushCategory,
                "intendedRecipientUserId": like.intendedRecipientUserId,
                "sourceUserId": like.sourceUserId,
                "account": like.account.igname,
                "created_at": like.created_at
            }
            likes.append(like_)
        
        response_data = {
            'count': paginator.page.paginator.count,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'results': likes,
        }
        
        return Response(response_data,status=status.HTTP_200_OK)
    
class CommentViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    with schema_context(os.getenv('SCHEMA_NAME')):queryset = Comment.objects.filter(account__isnull=False)
    serializer_class = CommentSerializer
    pagination_class = PaginationClass

    @schema_context(os.getenv('SCHEMA_NAME'))
    def create(self, request):
        title = request.data.get('title')
        message = request.data.get('message')
        media_id = request.data.get('media_id')
        target_comment_id = request.data.get('target_comment_id')
        collapse_key = request.data.get('collapse_key')
        optional_avatar_url = request.data.get('optional_avatar_url')
        push_id = request.data.get('push_id')
        push_category = request.data.get('push_category')
        intended_recipient_user_id = request.data.get('intended_recipient_user_id')
        source_user_id = request.data.get('source_user_id')

        # Get or create account based on title
        try:
            account, created = Account.objects.get_or_create(igname=title)
        except Exception as error:
            print(error)

        # Create a new comment instance
        comment_data = {
            'account': account.id,  # Use account ID for ForeignKey
            'message': message,
            'media_id': media_id,
            'comment_id': target_comment_id,
            'target_comment_id': target_comment_id,
            'collapseKey': collapse_key,
            'optionalAvatarUrl': optional_avatar_url,
            'pushId': push_id,
            'pushCategory': push_category,
            'intendedRecipientUserId': intended_recipient_user_id,
            'sourceUserId': source_user_id
        }

        # Initialize the serializer with the prepared data
        serializer = CommentSerializer(data=comment_data)


        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @schema_context(os.getenv('SCHEMA_NAME'))
    def list(self, request, pk=None):
        paginator = self.pagination_class()
        queryset = Comment.objects.all()
        result_page = paginator.paginate_queryset(queryset, request)  # Apply pagination
        comments = []
        
        for comment in result_page:
            comment_ = {
                "id": comment.id,
                "comment_id": comment.comment_id,
                "message": comment.message,
                "media_id": comment.media_id,
                "target_comment_id": comment.target_comment_id,
                "collapseKey": comment.collapseKey,
                "optionalAvatarUrl": comment.optionalAvatarUrl,
                "pushId": comment.pushId,
                "pushCategory": comment.pushCategory,
                "intendedRecipientUserId": comment.intendedRecipientUserId,
                "sourceUserId": comment.sourceUserId,
                "account": comment.account.igname,
                "created_at":comment.created_at
            }
            comments.append(comment_)
        
        response_data = {
            'count': paginator.page.paginator.count,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'results': comments,
        }
        
        return Response(response_data,status=status.HTTP_200_OK)
    
class AccountViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    with schema_context(os.getenv('SCHEMA_NAME')):queryset = Account.objects.all()
    serializer_class = AccountSerializer
    pagination_class = PaginationClass

    def get_serializer_class(self):
        if self.action == "batch_uploads":
            return UploadSerializer
        elif self.action == "retrieve":
            return GetSingleAccountSerializer
        elif self.action == "update":  # override update serializer
            return GetAccountSerializer
        elif self.action == "schedule-outreach":
            return ScheduleOutreachSerializer
        return self.serializer_class


    @schema_context(os.getenv('SCHEMA_NAME'))
    def create(self, request, *args, **kwargs):
        try:
            serializer = AccountSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        except Exception as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False, methods=['post'], url_path="create-account-manually")
    def create_account_manually(self, request):
        igname = request.data.get('igname')
        full_name = request.data.get('full_name')
        responded_date = request.data.get('responded_date')
        call_scheduled_date = request.data.get('call_scheduled_date')
        closing_date = request.data.get('closing_date')
        won_date = request.data.get('won_date')
        success_story_date = request.data.get('success_story_date')
        lost_date = request.data.get('lost_date')
        outreach_date = request.data.get('outreach_time')
        
        # Get or create account based on title
        try:
            print("****** creating account ********")
            account =  Account.objects.filter(igname=igname.strip()).first()
            
            if account is None:
                account,created = Account.objects.get_or_create(igname=igname.strip(),  
                                                                qualified=True,
                                                                outreach_success=False,
                                                                outreach_time=outreach_date,
                                                                responded_date=responded_date,
                                                                call_scheduled_date=call_scheduled_date,
                                                                closing_date=closing_date,
                                                                won_date=won_date,
                                                                success_story_date=success_story_date,
                                                                relevant_information={},
                                                                lost_date=lost_date,
                                                                full_name=full_name)
                OutSourced.objects.create(
                        results = {},
                        account = account
                    )
            else:
                account.qualified = True
                account.outreach_success = False
                account.outreach_time = outreach_date
                account.responded_date = responded_date
                account.call_scheduled_date = call_scheduled_date
                account.closing_date = closing_date
                account.won_date = won_date
                account.success_story_date = success_story_date
                account.lost_date = lost_date
                account.full_name = full_name
                if account.relevant_information is None:
                    account.relevant_information = {}
                if OutSourced.objects.filter(account=account).first() is None:
                    OutSourced.objects.create(
                        results = {},
                        account = account
                    )
                    
                    
                account.save()
                
                
            if outreach_date:
                account.outreach_success = True
                account.created_at = outreach_date
                account.status = StatusCheck.objects.get(name="sent_compliment")
                account.save()
                
                
          
            serializer = AccountSerializer(account)
            assign_salesrep(account)    
            return Response(serializer.data)
            # return Response(serializer_class(account).data, status=status.HTTP_201_CREATED)
        except Exception as error:
            print(error)
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)

    
    @schema_context(os.getenv('SCHEMA_NAME'))
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as error:
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)


    @schema_context(os.getenv('SCHEMA_NAME'))
    def list(self, request, pk=None): 
        queryset = Account.objects.filter(salesrep__isnull=False)
        # Apply annotations
        queryset = queryset.annotate(
            last_message_at=F('thread__last_message_at'),
            last_message_sent_at=Subquery(
                Message.objects.filter(thread=OuterRef('thread'))
                .order_by('-sent_on')
                .values('sent_on')[:1]
            ),
            last_message_sent_by=Subquery(
                Message.objects.filter(thread=OuterRef('thread'))
                .order_by('-sent_on')
                .values('sent_by')[:1]
            ),
            latest_message_at=Coalesce('last_message_sent_at', 'last_message_at', Value(datetime.min)),
            # thread_id=Subquery(Thread.objects.filter(account=OuterRef('pk')).values('thread_id')[:1])
        ).order_by('-created_at')#order_by('-latest_message_at')

        # Filters from request
        search_query = request.GET.get("q")
        created_at_gte = request.GET.get("created_at_gte")
        created_at_lt = request.GET.get("created_at_lt")
        status_param = request.GET.get('status_param')

        if search_query:
            queryset = queryset.filter(igname__icontains=search_query.strip())
        
        if status_param:
            if status_param.lower() == "null":
                queryset = queryset.filter(status_param__isnull=True)
            elif status_param.lower() == "blank":
                queryset = queryset.filter(status_param="")
            else:
                queryset = queryset.filter(status_param=status_param.strip())

        # Date parsing
        created_filter = {}
        if created_at_gte:
            created_filter["created_at__gte"] = make_aware(datetime.strptime(created_at_gte, "%Y-%m-%d"))

        if created_at_lt:
            created_filter["created_at__lt"] = make_aware(datetime.strptime(created_at_lt, "%Y-%m-%d")) + timedelta(days=1)

        if created_filter:
            queryset = queryset.filter(**created_filter)

        # Paginator for main list
        paginator = self.pagination_class()
        paginated_qs = paginator.paginate_queryset(queryset, request)
        serializer = self.get_serializer(paginated_qs, many=True)
        
        

        # Filtered sets with date range
        qualified_accounts = Account.objects.filter(qualified=True, outreach_success=False,**created_filter)
        
        

        today_start = make_aware(datetime.combine(now().date(), datetime.min.time()))
        tomorrow_start = today_start + timedelta(days=1)
        yesterday_start = today_start - timedelta(days=1)
        

        

        # yesterday's date range
        scheduled_accounts = Account.objects.filter(
            qualified=True,
            outreach_success=False,
            created_at__gte=today_start,
            created_at__lt=tomorrow_start
        )
        
        outreach_success_accounts = Account.objects.filter(
            outreach_success=True,
            created_at__gte=yesterday_start,
            created_at__lt=today_start
        )
        
        total_outreach = outreach_success_accounts.count()
        total_scheduled = qualified_accounts.count()
        
        
        return Response({
            "count": paginator.page.paginator.count,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": serializer.data,
            # "qualified": [],# AccountSerializer(qualified_accounts, many=True).data,
            "outreach_success": AccountSerializer(outreach_success_accounts, many=True).data,
            "scheduled": AccountSerializer(scheduled_accounts, many=True).data,
            "total_outreach": total_outreach,
            "total_scheduled": total_scheduled,
        })
    
    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False, methods=['get'], url_path="weekly-reporting")
    def weekly_reporting(self, request):
        # Get January 1st of the current year with timezone
        jan_first = datetime(datetime.now().year, 1, 1, tzinfo=timezone.get_current_timezone())
        # Adjust to the Monday of that week (0 = Monday, 6 = Sunday)
        start_of_week = jan_first - timedelta(days=jan_first.weekday())
        # start_of_year = datetime(datetime.now().year, 1, 1, tzinfo=timezone.get_current_timezone())
        today = timezone.now()
        current_week = start_of_week 
        results = []

        while current_week < today:
            next_week = current_week + timedelta(days=7)
            end_of_week = next_week - timedelta(seconds=1)

            outreach_accounts = Account.objects.filter(
                created_at__gte=current_week,
                created_at__lte=end_of_week,
                outreach_success=True,
            )
            outreach_count = outreach_accounts.count()
            
            print("Outrech count **",outreach_count)
            
            sales_qualified_accounts = Account.objects.filter(
                created_at__gte=current_week,
                created_at__lte=end_of_week,
                salesrep__isnull=False,
                responded_date__isnull=False,
                #call_scheduled_date__isnull=False,
                # won_date__isnull=True,
                lost_date__isnull=True
            )
            

            responded_messages = Message.objects.filter(
                sent_by='Client',
                sent_on__gte=current_week,
                sent_on__lte=end_of_week
            ).values_list('thread__account__igname', flat=True).distinct()

            responded_count = responded_messages.count()
            responded_rate = round((responded_count / outreach_count) * 100,2) if outreach_count > 0 else 0
            
            call_scheduled_date = Account.objects.filter(call_scheduled_date__range=(current_week, next_week)).count()
            call_scheduled_rate = round((call_scheduled_date / outreach_count) * 100) if outreach_count > 0 else 0
            closing_date = Account.objects.filter(closing_date__range=(current_week, next_week)).count()
            closing_rate = round((closing_date / outreach_count) * 100,2) if outreach_count > 0 else 0
            won_date = Account.objects.filter(won_date__range=(current_week, next_week)).count()
            won_rate = round((won_date / outreach_count) * 100,2) if outreach_count > 0 else 0
            success_story_date = Account.objects.filter(success_story_date__range=(current_week, next_week)).count()
            success_story_rate = round((success_story_date / outreach_count) * 100,2) if outreach_count > 0 else 0
            lost_date = Account.objects.filter(lost_date__range=(current_week, next_week)).count()
            lost_rate = round((lost_date / outreach_count) * 100,2) if outreach_count > 0 else 0
            responded_date = Account.objects.filter(responded_date__range=(current_week, next_week)).count()
            sq_conversion_rate = round((sales_qualified_accounts.count()/outreach_count) * 100,2) if outreach_count > 0 else 0
            
           

            results.append({
                "week_start": current_week.strftime("%Y-%m-%d"),
                "outreach": outreach_count,
                "outreach_list": list(outreach_accounts.values_list('igname', flat=True)),
                "responded": responded_count,
                "responded_ignames": list(responded_messages),
                "call_scheduled_date": call_scheduled_date,
                "closing_date": closing_date,
                "won_date": won_date,
                "success_story_date": success_story_date,
                "lost_date": lost_date,
                "lost_list": [],
                "responded_date": responded_date,
                "responded_rate": responded_rate,
                "call_scheduled_rate": call_scheduled_rate,
                "closing_rate": closing_rate,
                "won_rate": won_rate,
                "won_list": [],
                "success_story_rate": success_story_rate,
                "lost_rate": lost_rate,
                "sq_conversion_rate": sq_conversion_rate,
                "sales_qualified_count": sales_qualified_accounts.count(),
                "sales_qualified_accounts": list(sales_qualified_accounts.values_list('igname', flat=True)),
            })

            current_week = next_week
            
        return Response({
            "results": results
        })

    
    
    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=['post'], url_path="clear-convo")
    def clear_convo(self, request, **kwargs):
        account = self.get_object()
        
        try:
            # reset status
            account.status = None
            account.status_param = 'Prequalified'
            account.assigned_to = 'Robot'
            account.save()
            thread = account.thread_set.latest('created_at')
            thread.message_set.clear()
        except Exception as error:
            return Response({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({"success": True, "message": "Conversations successfully reset"}, status=status.HTTP_200_OK)
        
    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=['post'], url_path="add-notes")
    def add_notes(self, request, **kwargs):
        account = self.get_object()
        
        try:
            notes = request.data.get('notes')  # Extract 'notes' from the request data

            if not notes:
                return Response(
                    {"error": "Notes field is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            account.notes = notes

            account.save()

        except Exception as error:
            return Response({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(
            {"message": "Notes added successfully.", "notes": account.notes},
            status=status.HTTP_200_OK
        )    

    @schema_context(os.getenv('SCHEMA_NAME'))
    def retrieve(self, request, pk=None):
        queryset = Account.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = GetSingleAccountSerializer(user)
        return Response(serializer.data)

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False, methods=['get'], url_path="active-stages")
    def active_stages(self, request):
        # Retrieve all unique status_param values
        unique_status_params = Account.objects.values_list('status_param', flat=True).distinct()
        
        # Return as an array
        return Response(list(unique_status_params), status=status.HTTP_200_OK)

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False, methods=['get'], url_path="active-stage-stats")
    def active_stage_stats(self, request):
        # We'll add this filers as soon as we know when they moved from one stage to the next
        # start_date = request.GET.get("start_date")
        # end_date = request.GET.get("end_date")
        
        # if start_date:
        #     start_date = start_date.strip('"')
        # if end_date:
        #     end_date = end_date.strip('"')
        
        # start_date_parsed = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        # end_date_parsed = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        
        stages_with_counts = Account.objects.values('status_param') \
            .annotate(total_accounts=Count('status_param')) \
            .annotate(
                custom_order=Case(
                    When(status_param='Prequalified', then=0),
                    When(status_param='Sales Qualified', then=1),
                    When(status_param='Committed', then=2),
                    output_field=IntegerField()
                )
            )\
            .order_by('custom_order')
            
            # Fetch the counts for the specific transitions between stages based on the assumption
        prequalified_to_sales_qualified_count = Account.objects.filter(status_param='Sales Qualified').count()
        sales_qualified_to_committed_count = Account.objects.filter(status_param='Committed').count()

        # Calculate the total number of accounts in each stage
        prequalified_count = Account.objects.filter(status_param='Prequalified').count()
        sales_qualified_count = Account.objects.filter(status_param='Sales Qualified').count()

         # Calculate the percentages
        percentage_prequalified_to_sales_qualified = (prequalified_to_sales_qualified_count / prequalified_count * 100) if prequalified_count > 0 else 0
        percentage_sales_qualified_to_committed = (sales_qualified_to_committed_count / sales_qualified_count * 100) if sales_qualified_count > 0 else 0

        # Add the transition counts and percentages to the corresponding stages
        for stage in stages_with_counts:
            if stage['status_param'] == 'Committed':
                stage['sales_qualified_to_committed_count'] = sales_qualified_to_committed_count
                stage['percentage_sales_qualified_to_committed'] = percentage_sales_qualified_to_committed
            elif stage['status_param'] == 'Sales Qualified':
                stage['prequalified_to_sales_qualified_count'] = prequalified_to_sales_qualified_count
                stage['percentage_prequalified_to_sales_qualified'] = percentage_prequalified_to_sales_qualified

    
        # Return the results as a list of dictionaries
        return Response(stages_with_counts, status=status.HTTP_200_OK)
    
    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=['get'])
    def threads_with_messages(self, request, pk=None):
        """
        Retrieve all threads related to a specific account along with their messages,
        sorted by sent_on in descending order within each thread.
        """

        try:
            account = self.get_object()  # Get the account based on the pk
            threads = Thread.objects.filter(account=account).order_by('-last_message_at')  # Optionally order threads

            # Serialize the threads with nested messages
            serialized_data = ThreadMessageSerializer(threads, many=True).data
            account_serializer = GetSingleAccountSerializer(account).data

            return Response({
                'id': account.id,
                'igname': account.igname,
                'account': account_serializer,
                'threads': serialized_data
            })

        except Account.DoesNotExist:
            return Response({"error": "Account not found"}, status=404)
    
    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True,methods=["post"],url_path="add-outsourced")
    def add_outsourced(self,request,pk=None):
        account = self.get_object()
        outsourced_json = request.data.get("results")
        outsourced_source = request.data.get("source")
        outsourced = OutSourced.objects.create(source=outsourced_source,results=outsourced_json,account=account)
        return Response(
            {
                "message": "outsourced data saved succesfully",
                "id": outsourced.id,
                "result": outsourced.results,
                "source": outsourced.source
            }
        )
    
    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False,methods=["post"],url_path="get-id")
    def get_id(self,request,pk=None):
        username = request.data.get("username")
        account = Account.objects.filter(igname = username).latest('created_at')
        if account.outsourced_set.exists():
            return Response(
                {
                    "id": account.id,
                    "outsourced_id": account.outsourced_set.latest('created_at').id,
                    "qualified": account.qualified
                }
            )
        else:
            return Response(
                {
                    "id": account.id,
                    "qualified": account.qualified
                }
            )

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False,methods=['post'],url_path='qualify-account')
    def qualify_account(self, request, pk=None):
        account = Account.objects.filter(igname = request.data.get('username')).latest('created_at')
        accounts_qualified = []
        if account.outsourced_set.exists():
            account.qualified = request.data.get('qualify_flag')
            account.relevant_information = request.data.get("relevant_information")
            account.scraped = True
            account.save()
            accounts_qualified.append(
                {
                    "qualified":account.qualified,
                    "account_id":account.id
                }
            )
    
        return Response(accounts_qualified, status=status.HTTP_200_OK)
    
    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False,methods=['post'],url_path='manually-trigger')
    def manually_trigger(self, request, pk=None):
        account = Account.objects.filter(igname = request.data.get('username')).latest('created_at')
        accounts_triggered = []
        if account.outsourced_set.exists():
            account.is_manually_triggered = True
            account.save()
            accounts_triggered.append(
                {
                    "manually_triggered":account.is_manually_triggered,
                    "account_id":account.id
                }
            )
    
        return Response(accounts_triggered, status=status.HTTP_200_OK)

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["get"], url_path="potential-buy")
    def potential_buy(self, request, pk=None):
        account = self.get_object()
        status_code = 0
        cl = login_user()

        user_info = cl.user_info_by_username(account.igname).dict()
        potential_buy = 0
        l1 = ["hello", "hi"]
        l2 = user_info["biography"].split(" ")
        for i in l1:
            if l2.count(i) > 0:
                potential_buy = 50
                break
            status_code = 200

        return Response({"status_code": status_code, "potential_buy": potential_buy})

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["get"], url_path="potential-promote")
    def potential_promote(self, request, pk=None):
        account = self.get_object()
        status_code = 0
        cl = login_user()

        user_info = cl.user_info_by_username(account.igname).dict()
        l1 = ["hello", "hi"]
        l2 = user_info["biography"].split(" ")
        potential_promote = 0
        for i in l1:
            if l2.count(i) > 0:
                potential_promote = 50
                break
            status_code = 200

        return Response({"status_code": status_code, "potential_promote": potential_promote})
    
    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["get"], url_path="extract-followers")
    def extract_followers(self, request, pk=None):
        account = self.get_object()
        cl = login_user()

        user_info = cl.user_info_by_username(account.igname).dict()
        followers = cl.user_followers(user_info["pk"])
        for follower in followers:
            account_ = Account()
            account_.igname = followers[follower].username
            account_.save()
        return Response(followers)

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False, methods=["post"], url_path="batch-uploads")
    def batch_uploads(self, request):
        serializer = UploadSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)

        if valid:
            paramFile = io.TextIOWrapper(request.FILES["file_uploaded"].file)
            portfolio1 = csv.DictReader(paramFile)
            list_of_dict = list(portfolio1)
            objs = [Account(id=PushID().next_id(), igname=row["username"]) for row in list_of_dict]
            try:
                msg = Account.objects.bulk_create(objs)
                returnmsg = {"status_code": 200}
                print(f"imported {msg} successfully")
            except Exception as e:
                print("Error While Importing Data: ", e)
                returnmsg = {"status_code": 500}

            return Response(returnmsg)

        else:
            return Response({"status_code": 500})

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False, methods=["get"], url_path="extract-action-button", url_name="extract_action_button")
    def extract_action_bution(self, request):
        status_code = 0
        external_urls = []
        cl = login_user()

        for _, account in enumerate(self.queryset):
            try:
                url_info = cl.user_info_by_username(account.igname)
            except UserNotFound as err:
                logging.warning(err)

            account.competitor = urlparse(url_info.external_url).netloc
            account.save()
            external_url_info = {
                "external_url": url_info.external_url,
                "category": url_info.category,
                "competitor": account.competitor,
            }
            external_urls.append(external_url_info)
            status_code = status.HTTP_200_OK
            logging.warning(f"extracting info from => {account.igname}")

        response = {"actions": external_urls, "status_code": status_code}
        return Response(response)

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False, methods=["get"], url_path="needs-assessment", url_name="needs_assesment")
    def send_to_needs_assessment(self, request):

        account = self.get_object()
        account.stage = 2
        account.save()
        return Response({"stage": 2, "success": True})

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=['post'], url_path="reset-account")
    def reset_account(self, request, pk=None):
        account = self.get_object()

        Thread.objects.filter(account=account).delete()
        account.status = None
        account.confirmed_problems = ""
        account.rejected_problems = ""
        account.save()
        salesReps = SalesRep.objects.filter(instagram=account)
        for salesRep in salesReps:
            salesRep.instagram.remove(account)
        return Response({"message": "Account reset successfully"})

    @schema_context(os.getenv('SCHEMA_NAME'))
    def account_by_ig_thread_id(self, request, *args, **kwargs):
        # There could be more than one thread with the same thread id
        # thread = Thread.objects.get(thread_id=kwargs.get('ig_thread_id')) 
        thread = Thread.objects.filter(thread_id=kwargs.get('ig_thread_id')).first() 
        if thread.account:
            accounts = Account.objects.filter(id=thread.account.id)
            account = accounts.latest('created_at')
            serializer = GetSingleAccountSerializer(account)
            return Response(serializer.data)
        else:
            return Response({"error":"Account does not have thread attached"})
    
    @schema_context(os.getenv('SCHEMA_NAME'))
    def retrieve_salesrep(self, request, *args, **kwargs):
        username = kwargs.get('username')

        # Check if username is provided
        if not username:
            return Response({"error": "Username not provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the account object or return 404 if not found
        account = Account.objects.filter(igname=username).last()

        # Retrieve the last salesrep associated with the account
        salesrep = account.salesrep_set.last()

        # Check if salesrep is found
        if not salesrep:
            return Response({"error": "Salesrep not found for this account"}, status=status.HTTP_404_NOT_FOUND)

        # Convert salesrep object to dictionary
        salesrep_data = {
            "id": salesrep.id,
            "username": salesrep.ig_username,
        }

        return Response({"salesrep": salesrep_data}, status=status.HTTP_200_OK)
        
    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=['post'], url_path="schedule-outreach")
    def schedule_outreach(self, request, pk=None):
        serializer = ScheduleOutreachSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)
        account = self.get_object()
        if valid:
            available_sales_reps = SalesRep.objects.filter(available=True)
            random_salesrep_index = random.randint(0,len(available_sales_reps)-1)
            available_sales_reps[random_salesrep_index].instagram.add(account)

            schedule = CrontabSchedule.objects.create(
                minute=serializer.data.get('minute'),
                hour=serializer.data.get('hour'),
                day_of_week="*",
                day_of_month=serializer.data.get('day_of_month'),
                month_of_year=serializer.data.get('month_of_year'),
            )
            try:
                PeriodicTask.objects.update_or_create(
                    name=f"SendFirstCompliment-{account.igname}",
                    crontab=schedule,
                    task="instagram.tasks.send_first_compliment",
                    args=json.dumps([[account.igname]])
                )
                
            except Exception as error:
                logging.warning(error)

            return Response(serializer.data,status=status.HTTP_200_OK)
        else:
            return Response({"error": True})

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False, methods=["get"], url_path="get-connected-accounts")
    def get_connected_accounts(self, request, pk=None):
        response = requests.get(settings.MQTT_BASE_URL+"/accounts/connected")
        print(response.status_code)
        
        if response.status_code == 200:
            print(json.loads(response.content))
            print(response.json)
            
            return Response(
                    {
                        "status": status.HTTP_200_OK,
                        "mqtt_running": True,
                        "mqtt_connected": True,
                        "connected_accounts": json.loads(response.content),
                        "success": True,
                    }
                )
        else:
            return Response(
                    {
                        "status": response.status_code,
                        "mqtt_running": False,
                        "mqtt_connected": False,
                        "connected_accounts": [],
                        "success": True,
                    }
                )
            
    @action(detail=False, methods=["get"], url_path="get-loggedin-accounts")
    def get_loggedin_accounts(self, request, pk=None):
        response = requests.get(settings.MQTT_BASE_URL+"/accounts/loggedin")
        
        if response.status_code == 200:
            
            return Response(
                    {
                        "status": status.HTTP_200_OK,
                        "mqtt_running": True,
                        "mqtt_connected": True,
                        "connected_accounts": json.loads(response.content),
                        "success": True,
                    }
                )
        else:
            return Response(
                    {
                        "status": response.status_code,
                        "mqtt_running": False,
                        "mqtt_connected": False,
                        "connected_accounts": [],
                        "success": True,
                    }
                )
    
    @action(detail=False, methods=["get"], url_path="check-mqtt-health")
    def get_mqtt_heath(self, request, pk=None):
        response = requests.get(settings.MQTT_BASE_URL+"/health")
        
        if response.status_code == 200:
             return Response(
                    {
                        "status": status.HTTP_200_OK,
                        "mqtt_running": True,
                        "mqtt_connected": True,
                        "success": True,
                    }
                )
        else:
            return Response(
                    {
                        "status": response.status_code,
                        "mqtt_running": False,
                        "mqtt_connected": False,
                        "success": True,
                    }
                )
            
    @action(detail=False, methods=["get"], url_path="get-comments")
    def get_mqtt_comments(self, request, pk=None):
        status_param = request.GET.get('username')
        media_id = request.GET.get('media_id')
        data = {"username_from": 'denn_mokaya', "media_id": '1263679849772992148'}
        response = requests.post(settings.MQTT_BASE_URL+"/fetchComments", data=json.dumps(data))
        print("hdhdhdh")
        if response.status_code == 200:
             return Response(
                    {
                        "status": status.HTTP_200_OK,
                        "data": json.loads(response.content),
                        "success": True,
                    }
                )
        else:
            return Response(
                    {
                        "status": response.status_code,
                        "data": [],
                        "success": False,
                    }
                )
            
    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False, methods=["get"], url_path="handle-duplicates")
    def find_handle_duplicates(self, request):
        duplicate_igname_list = (
            Account.objects.values('igname')
            .annotate(igname_count=Count('igname'))
            .filter(igname_count__gt=1)
            .values_list('igname', flat=True)
        )
        print(f"How many duplicates? {len(duplicate_igname_list)}")
        if len(duplicate_igname_list) > 0:
            delete_accounts.delay(duplicate_igname_list)
        else:
            print("No duplicates have been found in the system.")
        return Response({
            "handled":True,
            "found": len(duplicate_igname_list)
        }, status = status.HTTP_202_ACCEPTED)
    
    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False, methods=["post"], url_path="qualify-test-accounts")
    def qualify_test_accounts(self, request):
        # test_account = Account.objects.filter(igname__icontains=request.data.get("igname")).latest('created_at')
        try:
            test_account = Account.objects.filter(igname__icontains=request.data.get("igname")).latest('created_at')
        except Account.DoesNotExist:
            return Response({"error": "No matching test account found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            UnwantedAccount.objects.filter(username__icontains=test_account.igname).delete()
        except Exception as error:
            return Response({"error": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        try:
            # reset lead
            test_account.qualified = True
            test_account.created_at = timezone.now()
            test_account.status = None
            test_account.status_param = 'Prequalified'
            test_account.assigned_to = 'Robot'
            test_account.save()
            if test_account.thread_set.exists():
                thread = test_account.thread_set.latest('created_at')
                thread.message_set.clear()
        except Exception as error:
            return Response({"error": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({"status": status.HTTP_200_OK, "message": "Test account successfully qualified."})

    @action(detail=False,methods=['post'],url_path='prequalify-accounts')
    def prequalify_accounts(self, request, pk=None):
        prequalify_task.delay() 
        
        return Response({"message":"Succesfully qualified accounts"}, status=status.HTTP_200_OK)

class HashTagViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    with schema_context(os.getenv('SCHEMA_NAME')):queryset = HashTag.objects.all()
    serializer_class = HashTagSerializer

    def get_serializer_class(self):
        if self.action == "batch_uploads":
            return UploadSerializer
        return self.serializer_class

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False, methods=["post"], url_path="batch-uploads")
    def batch_uploads(self, request):
        serializer = UploadSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)

        if valid:
            paramFile = io.TextIOWrapper(request.FILES["file_uploaded"].file)
            portfolio1 = csv.DictReader(paramFile)
            list_of_dict = list(portfolio1)
            objs = [HashTag(id=PushID().next_id(), name=row["name"]) for row in list_of_dict]
            try:
                msg = HashTag.objects.bulk_create(objs)
                returnmsg = {"status_code": 200}
                print(f"imported {msg} successfully")
            except Exception as e:
                print("Error While Importing Data: ", e)
                returnmsg = {"status_code": 500}

            return Response(returnmsg)

        else:
            return Response({"status_code": 500})


class PhotoViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    with schema_context(os.getenv('SCHEMA_NAME')):queryset = Photo.objects.all()
    serializer_class = PhotoSerializer

    def get_serializer_class(self):
        if self.action == "batch_uploads":
            return UploadSerializer
        elif self.action == "add_comment":
            return AddContentSerializer
        return self.serializer_class

    @schema_context(os.getenv('SCHEMA_NAME'))
    def perform_create(self, request, *args, **kwargs):
        cl = login_user()
        serializer = self.get_serializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)
        photo = Photo(**serializer.data)
        if valid:
            media_pk = cl.media_pk_from_url(serializer.data.get("link"))
            user = cl.media_user(media_pk=media_pk)
            account = Account.objects.filter(igname=user.username)
            if account.exists():
                photo.account = account.last()
                photo.save()
            else:
                account = Account()
                account.igname = user.username
                account.save()
                photo.save()

        return Response({"data": serializer.data})

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["get"], url_path="retrieve-likers")
    def retrieve_likers(self, request, pk=None):
        photo = self.get_object()
        cl = login_user()

        media_pk = cl.media_pk_from_url(photo.link)
        likers = cl.media_likers(media_pk)
        for liker in likers:
            account = Account()
            account.igname = liker.username
            account.save()
        return Response(likers)

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["get"], url_path="fetch-comments")
    def fetch_comments(self, request, pk=None):
        try:
            photo = self.get_object()
            cl = login_user()
            media_pk = cl.media_pk_from_url(photo.link)
            media_id = cl.media_id(media_pk=media_pk)
            comments = cl.media_comments(media_id=media_id)

            response = {"comments": comments, "length": len(comments), "owner": photo.account.igname}
            return Response(response, status=status.HTTP_200_OK)
        except Exception as error:
            error_message = str(error)
            return Response({"error": error_message})

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["post"], url_path="generate-comment")
    def generate_comment(self, request, pk=None):
        photo = self.get_object()
        generated_response = detect_intent(
            project_id="boostedchatapi",
            session_id=str(uuid.uuid4()),
            message=request.data.get("text"),
            language_code="en",
        )
        return Response(
            {
                "status": status.HTTP_200_OK,
                "generated_comment": generated_response,
                "text": request.data.get("text"),
                "photo": photo.link,
                "success": True,
            }
        )

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False, methods=["post"], url_path="batch-uploads")
    def batch_uploads(self, request):
        serializer = UploadSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)

        if valid:
            paramFile = io.TextIOWrapper(request.FILES["file_uploaded"].file)
            portfolio1 = csv.DictReader(paramFile)
            list_of_dict = list(portfolio1)
            objs = [Photo(id=PushID().next_id(), link=row["link"]) for row in list_of_dict]
            try:
                msg = Photo.objects.bulk_create(objs)
                returnmsg = {"status_code": 200}
                print(f"imported {msg} successfully")
            except Exception as e:
                print("Error While Importing Data: ", e)
                returnmsg = {"status_code": 500}

            return Response(returnmsg)

        else:
            return Response({"status_code": 500})


class VideoViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    with schema_context(os.getenv('SCHEMA_NAME')):queryset = Video.objects.all()
    serializer_class = VideoSerializer

    def get_serializer_class(self):
        if self.action == "batch_uploads":
            return UploadSerializer
        elif self.action == "add_comment":
            return AddContentSerializer
        return self.serializer_class

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["get"], url_path="fetch-comments")
    def fetch_comments(self, request, pk=None):
        try:
            video = self.get_object()
            cl = login_user()
            media_pk = cl.media_pk_from_url(video.link)
            media_id = cl.media_id(media_pk=media_pk)
            comments = cl.media_comments(media_id=media_id)
            response = {"comments": comments, "length": len(comments)}
            return Response(response, status=status.HTTP_200_OK)
        except Exception as error:
            error_message = str(error)
            return Response({"error": error_message})

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["post"], url_path="generate-comment")
    def generate_comment(self, request, pk=None):
        video = self.get_object()
        generated_response = detect_intent(
            project_id="boostedchatapi",
            session_id=str(uuid.uuid4()),
            message=request.data.get("text"),
            language_code="en",
        )
        return Response(
            {
                "status": status.HTTP_200_OK,
                "generated_comment": generated_response,
                "text": request.data.get("text"),
                "video": video.link,
                "success": True,
            }
        )

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["get"], url_path="retrieve-likers")
    def retrieve_likers(self, request, pk=None):
        video = self.get_object()
        cl = login_user()

        media_pk = cl.media_pk_from_url(video.link)
        likers = cl.media_likers(media_pk)
        for liker in likers:
            account = Account()
            account.igname = liker.username
            account.save()
        return Response(likers)

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["get"], url_path="retrieve-commenters")
    def retrieve_commenters(self, request, pk=None):
        video = self.get_object()
        cl = login_user()

        media_pk = cl.media_pk_from_url(video.link)
        comments = cl.media_comments(media_pk)
        for comment in comments:
            account = Account()
            account.igname = comment.user.username
            account.save()
        return Response(comments)

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False, methods=["post"], url_path="batch-uploads")
    def batch_uploads(self, request):
        serializer = UploadSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)

        if valid:
            paramFile = io.TextIOWrapper(request.FILES["file_uploaded"].file)
            portfolio1 = csv.DictReader(paramFile)
            list_of_dict = list(portfolio1)
            objs = [Video(id=PushID().next_id(), link=row["link"]) for row in list_of_dict]
            try:
                msg = Video.objects.bulk_create(objs)
                returnmsg = {"status_code": 200}
                print(f"imported {msg} successfully")
            except Exception as e:
                print("Error While Importing Data: ", e)
                returnmsg = {"status_code": 500}

            return Response(returnmsg)

        else:
            return Response({"status_code": 500})


class ReelViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    with schema_context(os.getenv('SCHEMA_NAME')):queryset = Reel.objects.all()
    serializer_class = ReelSerializer

    def get_serializer_class(self):
        if self.action == "batch_uploads":
            return UploadSerializer
        elif self.action == "add_comment":
            return AddContentSerializer

        return self.serializer_class

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["get"], url_path="fetch-comments")
    def fetch_comments(self, request, pk=None):
        try:
            reel = self.get_object()
            cl = login_user()
            media_pk = cl.media_pk_from_url(reel.link)
            media_id = cl.media_id(media_pk=media_pk)
            comments = cl.media_comments(media_id=media_id)
            response = {"comments": comments, "length": len(comments)}
            return Response(response, status=status.HTTP_200_OK)
        except Exception as error:
            error_message = str(error)
            return Response({"error": error_message})

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["post"], url_path="generate-comment")
    def generate_comment(self, request, pk=None):
        reel = self.get_object()
        generated_response = detect_intent(
            project_id="boostedchatapi",
            session_id=str(uuid.uuid4()),
            message=request.data.get("text"),
            language_code="en",
        )
        return Response(
            {
                "status": status.HTTP_200_OK,
                "generated_comment": generated_response,
                "text": request.data.get("text"),
                "reel": reel.link,
                "success": True,
            }
        )

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["post"], url_path="add-comment")
    def add_comment(self, request, pk=None):
        reel = self.get_object()
        cl = login_user()

        media_pk = cl.media_pk_from_url(reel.link)
        media_id = cl.media_id(media_pk=media_pk)
        serializer = AddContentSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)
        generated_response = serializer.data.get("generated_response")
        if valid and serializer.data.get("assign_robot") and serializer.data.get("approve"):
            cl.media_comment(media_id, generated_response)
            return Response({"status": status.HTTP_200_OK, "message": generated_response, "success": True})
        else:
            cl.media_comment(media_id, serializer.data.get("human_response"))
            return Response(
                {"status": status.HTTP_200_OK, "message": serializer.data.get("human_response"), "success": True}
            )

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["get"], url_path="retrieve-likers")
    def retrieve_likers(self, request, pk=None):
        reel = self.get_object()
        cl = login_user()

        media_pk = cl.media_pk_from_url(reel.link)
        likers = cl.media_likers(media_pk)
        for liker in likers:
            account = Account()
            account.igname = liker.username
            account.save()
        return Response(likers)

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["get"], url_path="retrieve-commenters")
    def retrieve_commenters(self, request, pk=None):
        reel = self.get_object()
        cl = login_user()

        media_pk = cl.media_pk_from_url(reel.link)
        comments = cl.media_comments(media_pk)
        for comment in comments:
            account = Account()
            account.igname = comment.user.username
            account.save()
        return Response(comments)

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False, methods=["post"], url_path="batch-uploads")
    def batch_uploads(self, request):
        serializer = UploadSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)

        if valid:
            paramFile = io.TextIOWrapper(request.FILES["file_uploaded"].file)
            portfolio1 = csv.DictReader(paramFile)
            list_of_dict = list(portfolio1)
            objs = [Reel(id=PushID().next_id(), link=row["link"]) for row in list_of_dict]
            try:
                msg = Reel.objects.bulk_create(objs)
                returnmsg = {"status_code": 200}
                print(f"imported {msg} successfully")
            except Exception as e:
                print("Error While Importing Data: ", e)
                returnmsg = {"status_code": 500}

            return Response(returnmsg)

        else:
            return Response({"status_code": 500})




class StoryViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    with schema_context(os.getenv('SCHEMA_NAME')):queryset = Story.objects.all()
    serializer_class = StorySerializer

    def get_serializer_class(self):
        if self.action == "batch_uploads":
            return UploadSerializer
        elif self.action == "add_comment":
            return AddContentSerializer
        return self.serializer_class

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["get"], url_path="fetch-comments")
    def fetch_comments(self, request, pk=None):
        try:
            story = self.get_object()
            cl = login_user()
            media_pk = cl.media_pk_from_url(story.link)
            media_id = cl.media_id(media_pk=media_pk)
            comments = cl.media_comments(media_id=media_id)
            response = {"comments": comments, "length": len(comments)}
            return Response(response, status=status.HTTP_200_OK)
        except Exception as error:
            error_message = str(error)
            return Response({"error": error_message})

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["post"], url_path="generate-comment")
    def generate_comment(self, request, pk=None):
        story = self.get_object()
        generated_response = detect_intent(
            project_id="boostedchatapi",
            session_id=str(uuid.uuid4()),
            message=request.data.get("text"),
            language_code="en",
        )
        return Response(
            {
                "status": status.HTTP_200_OK,
                "generated_comment": generated_response,
                "text": request.data.get("text"),
                "story": story.link,
                "success": True,
            }
        )

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["post"], url_path="add-comment")
    def add_comment(self, request, pk=None):
        story = self.get_object()
        cl = login_user()

        media_pk = cl.media_pk_from_url(story.link)
        media_id = cl.media_id(media_pk=media_pk)
        serializer = AddContentSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)
        generated_response = serializer.data.get("generated_response")
        if valid and serializer.data.get("assign_robot") and serializer.data.get("approve"):
            cl.media_comment(media_id, generated_response)
            return Response({"status": status.HTTP_200_OK, "message": generated_response, "success": True})
        else:
            cl.media_comment(media_id, serializer.data.get("human_response"))
            return Response(
                {"status": status.HTTP_200_OK, "message": serializer.data.get("human_response"), "success": True}
            )

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["get"], url_path="retrieve-info")
    def like_story(self, request, pk=None):
        story = self.get_object()
        cl = login_user()
        story_pk = cl.story_pk_from_url(story.link)
        info = cl.story_info(story_pk)
        cl.story_like(story_id=info.id)
        return Response({"status": status.HTTP_200_OK, "success": True})

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["get"], url_path="retrieve-info")
    def retrieve_info(self, request, pk=None):
        story = self.get_object()
        cl = login_user()

        story_pk = cl.story_pk_from_url(story.link)
        info = cl.story_info(story_pk).dict()
        return Response(info)

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False, methods=["post"], url_path="batch-uploads")
    def batch_uploads(self, request):
        serializer = UploadSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)

        if valid:
            paramFile = io.TextIOWrapper(request.FILES["file_uploaded"].file)
            portfolio1 = csv.DictReader(paramFile)
            list_of_dict = list(portfolio1)
            objs = [Story(id=PushID().next_id(), link=row["link"]) for row in list_of_dict]
            try:
                msg = Story.objects.bulk_create(objs)
                returnmsg = {"status_code": 200}
                print(f"imported {msg} successfully")
            except Exception as e:
                print("Error While Importing Data: ", e)
                returnmsg = {"status_code": 500}

            return Response(returnmsg)

        else:
            return Response({"status_code": 500})


class DMViewset(viewsets.ModelViewSet):
    with schema_context(os.getenv('SCHEMA_NAME')):queryset = Thread.objects.all()
    serializer_class = ThreadSerializer
    pagination_class = PaginationClass

    def get_serializer_class(self):
        if self.action == "send_message":
            return AddContentSerializer
        elif self.action == "generate_response":
            return AddContentSerializer
        return self.serializer_class

    @schema_context(os.getenv('SCHEMA_NAME'))
    def list(self, request, pk=None):
        assigned_to_filter = request.GET.get("assigned_to")
        stage_filter = request.GET.get("stage")
        salesrep_filter = request.GET.get("sales_rep")
        search_query = request.GET.get("q")
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        paginator = self.pagination_class()
       
        if start_date:
            start_date = start_date.strip('"')
        if end_date:
            end_date = end_date.strip('"')
    
        start_date_parsed = parse_datetime(start_date ) if start_date else None
        end_date_parsed = parse_datetime(end_date) if end_date else None
        
       
        print("8888888888888888888")
        print(start_date)
        print(start_date_parsed)
        queryset = Thread.objects.select_related('account').filter(account__salesrep__isnull=False).annotate(last_message_at_ordering=Coalesce('last_message_at', Value(datetime.min))).order_by(F('last_message_at_ordering').desc())
        message_data = []
        messages = None
          # Apply date range filter if both start_date and end_date are provided
        # if start_date and end_date:
        #     try:
        #         # Parse the dates and filter the queryset
        #         start_date_parsed = parse_date(start_date)
        #         end_date_parsed = parse_date(end_date)
        #         if start_date_parsed and end_date_parsed:
        #             queryset = queryset.filter(
        #                 last_message_at__gte=start_date_parsed,
        #                 last_message_at__lte=end_date_parsed
        #                 )
        #     except ValueError:
        #         pass  
         # Use start_date as both start and end if only start_date is provided
        if start_date_parsed:
            if end_date_parsed:
                # Both dates are present
                queryset = queryset.filter(
                    last_message_at__gte=start_date_parsed,
                    last_message_at__lte=end_date_parsed
                )
            else:
                # Only start_date is present; use it as both
                print("kkkkkkkkkkkkkkkkkkkkkkk")
                print(start_date)
                print(start_date_parsed)
                queryset = queryset.filter(
                    last_message_at__date=start_date_parsed.date() 
                )
        elif end_date_parsed:
            # If only end_date is present, you can decide how to handle it
            queryset = queryset.filter(last_message_at__date=end_date_parsed.date())


        # Show only threads that have sales reps & order by last_message_at    
       

        if stage_filter is not None:
            queryset = queryset.filter(account__index__in=json.loads(stage_filter))
        if assigned_to_filter is not None:
            queryset = queryset.filter(account__assigned_to=assigned_to_filter)
        if salesrep_filter is not None:
            queryset = queryset.filter(account__salesrep__pk__in=json.loads(salesrep_filter))
        if search_query is not None:
            query = Q(account__igname__icontains=search_query) | Q(message__content__icontains=search_query)
            message_query = Q(content__icontains=search_query)
            messages = Message.objects.filter(message_query)
            messages_page = paginator.paginate_queryset(messages, request)
            for message in messages_page:
                message_data.append(
                    {
                        "id": message.id,
                        "thread_pk":message.thread.id,
                        "thread_id":message.thread.thread_id,
                        "content":message.content,
                        "sent_on":message.sent_on,
                        "username": message.thread.account.igname
                    }
                )                

            queryset = queryset.annotate(
                matching_messages_count=Count('message', filter=query)
            )
            queryset = queryset.filter(matching_messages_count__gt=0).distinct()

            
        
        result_page = paginator.paginate_queryset(queryset, request)
        serializer = ThreadSerializer(result_page, many=True)

        response_data = {
            'count': paginator.page.paginator.count,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'results': serializer.data,
            'messages': message_data if search_query is not None else []
        }



        return Response(response_data)

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False, methods=["get"], url_path="handle-duplicates")
    def find_handle_duplicates(self, request):
        duplicate_igname_list = (
            Account.objects.values('igname')
            .annotate(igname_count=Count('igname'))
            .filter(igname_count__gt=1)
            .values_list('igname', flat=True)
        )
        print(f"How many duplicates? {len(duplicate_igname_list)}")
        if len(duplicate_igname_list) > 0:
            for igname in duplicate_igname_list:
                accounts = Account.objects.filter(igname=igname).order_by('-created_at')
                accounts_to_delete = accounts[1:]  # Keep the latest one, delete the rest
                delete_count = Account.objects.filter(id__in=[acc.id for acc in accounts_to_delete]).delete()
                print(f"Deleted {delete_count} duplicate(s) for igname: {igname}")
        else:
            print("No duplicates have been found in the system.")
        return Response({
            "handled":True
        }, status = status.HTTP_202_ACCEPTED)

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False,methods=['post'],url_path="create-with-account")
    def create_with_account(self, request):
        account = get_object_or_404(Account,id = request.data.pop('account_id'))
        print(request.data)
        print(account)
        thread = Thread.objects.create(**request.data,account=account)
        return Response({'id':thread.id}, status=status.HTTP_200_OK)


    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False, methods=["post"], url_path="download-csv")
    def download_csv(self, request):
        date_format = "%Y-%m-%d %H:%M:%S"
        date_string = request.data.get('date')
        datetime_object = datetime.strptime(date_string, date_format)
        datetime_object_utc = datetime_object.replace(tzinfo=timezone.utc)
        threads = self.queryset.filter(created_at__gte=datetime_object_utc)
        accounts = []
        for thread in threads:
            account_logs = LogEntry.objects.filter(object_pk=thread.account.pk)
            for log in account_logs:
                if "index" in log.changes_dict.keys():
                    accounts.append({
                        "username": thread.account.igname,
                        "assigned_to": thread.account.assigned_to,
                        "current_stage": thread.account.index,
                        "date_outreach_began": thread.created_at,
                        "timestamp":log.timestamp,
                        **log.changes_dict
                        
                    })
        return Response(accounts, status=status.HTTP_200_OK)

    
    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False, methods=["get"], url_path="response-rate")
    def response_rate(self, request):
        response_rate_object = []
        count = 0
        for thread in self.queryset:
            client_response = Message.objects.filter(
                Q(thread__thread_id=thread.thread_id) & Q(sent_by='Client')).order_by('-sent_on')
            if client_response.exists():
                count += 1
                response_rate_object.append(
                    {
                        "index": count,
                        "account": thread.account.igname,
                        "stage": thread.account.index
                    })
        return Response(data=response_rate_object, status=status.HTTP_200_OK)

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["post"], url_path="save-client-message")
    def save_client_message(self, request, pk=None):
        thread = self.get_object()

        # check if the message is already saved
        last_message = Message.objects.filter(Q(thread__thread_id=thread.thread_id)
                                              & Q(sent_by='Client')).order_by('-sent_on').first()
        if request.data.get("text") != last_message.content:
            try:
                # Save client message from here
                Message.objects.update_or_create(
                    content=request.data.get("text"),
                    sent_by="Client",
                    sent_on=timezone.now(),
                    thread=thread
                )
            except Exception as error:
                print(error)
        return Response({"success": True}, status=status.HTTP_201_CREATED)

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["post"], url_path="save-salesrep-message")
    def save_salesrep_message(self, request, pk=None):
        thread = self.get_object()

        last_message = Message.objects.filter(Q(thread__thread_id=thread.thread_id)
                                              & Q(sent_by='Robot')).order_by('-sent_on').first()
        if request.data.get("text") != last_message.content:
            try:
                Message.objects.update_or_create(
                    content=request.data.get("text"),
                    sent_by="Robot",
                    sent_on=timezone.now(),
                    thread=thread
                )
            except Exception as error:
                print(error)
        return Response({"success": True}, status=status.HTTP_201_CREATED)

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["post"], url_path="send-message-manually")
    def send_message_manually(self, request, pk=None):
        thread = self.get_object()

        serializer = SendManualMessageSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):

            account = thread.account
            salesrep = account.salesrep_set.last().ig_username
            data = {"message": serializer.data.get("message"), "username_to": account.igname, "username_from": salesrep}
            response = requests.post(settings.MQTT_BASE_URL+"/send-message", data=json.dumps(data))

            if response.status_code == 200:

                account.assigned_to = serializer.data.get("assigned_to")
                account.save()

                message = Message()
                message.content = serializer.data.get("message")
                message.sent_by = "Human"
                message.sent_on = timezone.now() #check:task we willl need to use correct timezone
                message.thread = thread
                message.save()

                thread.last_message_content = serializer.data.get("message")
                thread.last_message_at = timezone.now()
                thread.save()

                return Response(
                    {
                        "status": status.HTTP_200_OK,
                        "message": "Message sent successfully",
                        "thread_id": thread.thread_id,
                        "success": True,
                    }
                )
            else:
                return Response(
                    {
                        "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "message": "There was a problem sending your message",
                        "thread_id": thread.thread_id,
                        "success": True
                    }
                )
        else:
            return Response(
                {
                    "status": status.HTTP_200_OK,
                    "message": serializer.errors(),
                    "thread_id": thread.thread_id,
                    "success": True
                }
            )
    
    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False, methods=["post"], url_path="sync-messages")
    def sync_messages(self, request, *args, **kwargs):
        # Get data from request
        thread_id = request.data.get("threadId")
        messages = request.data.get('messages')
        igname = request.data.get('igname')
        number_of_messages_prior = Message.objects.count()
        
        if not thread_id or not messages:
            return Response({"error": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Find the thread
            thread = Thread.objects.get(thread_id=thread_id)
            print("Thread FOUND!")
        except Thread.DoesNotExist:
            # check if any message here includes the influecer
            # if so create the thread and save the messages 
            # if not skip this guy
            print("Thread NOT FOUND! creating ONE")
            accounts = Account.objects.filter(igname=igname)
            account = None
            # check if account exists
            if accounts.exists():
                account = accounts.latest('created_at')
                account.assigned_to = 'Human' # NB: this is a temporary fix
                account.save()
                print("ACCOUNT EXISTS!")
            # else: # if not create one
            #     account = Account()
            #     account.igname = igname
            #     account.created_at = timezone.now() - timezone.timedelta(days=5)
            #     account.qualified = True
            #     account.scraped = True
            #     account.status = StatusCheck.objects.get(name="sent_compliment")
            #     account.relevant_information = {"username":igname}
            #     account.save()
            #     try: # generate new outsourced information for it
            #         OutSourced.objects.create(results={"username":igname},account=account)
            #     except Exception as err:
            #         logging.warning(err)

                

            if account:
                print("LEAD EXISTS CREATING A NEW THREAD!")
                thread = Thread()
                thread.thread_id = thread_id
                thread.account = account
                thread.save()
                print("Thread CREATED A NEW THREAD!")
            else:
                return Response({"error": "LEAD DOES NOT EXIST"}, status=status.HTTP_404_NOT_FOUND)

        try:
        # Iterate through the messages
            for message in  messages:
                user_id = message.get("userId")
                content = message.get("content")
                message_id = message.get("messageId")
                timestamp = message.get("timestamp")
                content_data = message.get("contentData")
                content_type = message.get("itemType")
                
                # Convert microseconds to seconds
                timestamp_seconds = int(timestamp) / 1_000_000

                # Create a datetime object from the timestamp
                formatted_time = datetime.fromtimestamp(timestamp_seconds, tz=timezone2.utc)
                # datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)


                # Skip if any critical information is missing
                if not user_id or not content or not message_id or not timestamp:
                    print(f"Skipping message with incomplete data: {message}")
                    continue

                # Check if the message already exists
                if user_id == 'client':
                    existing_message = Message.objects.filter(sent_by="Client", thread=thread, content=content).first()
                    if existing_message:
                        # we can update the message id
                        print(f"Message already exists: {message_id}", content_data)
                        existing_message.message_id = message_id
                        existing_message.content_data = content_data
                        existing_message.content_type = content_type
                        existing_message.save()
                        continue

                    # Create the message
                    Message.objects.create(
                        thread=thread,
                        sent_by="Client",
                        # user_id=user_id,
                        content=content,
                        message_id=message_id,
                        sent_on=formatted_time,
                        content_type = content_type,
                        content_data = content_data,
                    )
                    
                    print(f"Client Message created: {message_id}")
                else:
                    existing_message = Message.objects.filter(sent_by="Robot", thread=thread, content=content).first()
                    if existing_message:
                        # we can update the message id
                        print(f"Message already exists: {message_id}")
                        existing_message.message_id = message_id
                        content_type = content_type,
                        content_data = content_data,
                        existing_message.save()
                        continue

                    # Create the message
                    Message.objects.create(
                        thread=thread,
                        sent_by="Robot",
                        # user_id=user_id,
                        content=content,
                        message_id=message_id,
                        sent_on=formatted_time,
                        content_type=content_type,
                        content_data=content_data
                    )
                    
                    print(f"Influener Message created: {message_id}")
            if Message.objects.count() > number_of_messages_prior:
                try:
                    subject = 'Hello Team'
                    message = f'Hooray! New messages have been synced. {Message.objects.count() - number_of_messages_prior} new messages have been added to the database.'
                    from_email = 'lutherlunyamwi@gmail.com'
                    recipient_list = ['dennorina@gmail.com','lutherlunyamwi@gmail.com','tomek@boostedchat.com']
                    send_mail(subject, message, from_email, recipient_list)
                except Exception as error:
                    logging.warning(error)

                return Response({"success": True}, status=status.HTTP_201_CREATED)
                
            else:
                return Response({"message": "No new messages"}, status=status.HTTP_201_CREATED)
            
        except Exception as e:  
            return Response({"success": False, "message": e}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

    @schema_context(os.getenv('SCHEMA_NAME'))
    def generate_outreach_times(self, request, *args,**kwargs):
        start_time = request.data.get("start_time")
        end_time = requests.data.get("end_time")
        slots = request.data.get("slots")
        time_slots = generate_time_slots(start_time, end_time, slots)
        # make it dynamic
        for time_slot in time_slots:
            try:
                OutreachTime.objects.update_or_create(time_slot)
            except Exception as err:
                print(err)
            print(time_slot)
        return Response({"message":"time slots successfully generated"})

    @schema_context(os.getenv('SCHEMA_NAME'))    
    def check_account_exists(self,request,*args,**kwargs):
        account = Account.objects.filter(igname = request.data.get('username'))
        if account.exists():
            return Response({"exists":True})
        else:
            return Response({"exists":False})
        
    @schema_context(os.getenv('SCHEMA_NAME'))
    def check_thread_exists(self,request,*args,**kwargs):
        account = Account.objects.filter(igname = request.data.get('username')).latest('created_at')
        if account.thread_set.exists():
            return Response({"exists":True})
        else:
            return Response({"exists":False})

    
    def is_time_slot_within_window(self, time_slot):
        # Set the Miami timezone (UTC-4)
        miami_tz = pytz.timezone('US/Eastern')  # Adjusts for DST
        
        # Convert time_slot to Miami timezone if it's not already
        if time_slot.tzinfo != miami_tz:
            time_slot = time_slot.astimezone(miami_tz)
        
        # Define the desired time window in Miami time
        start_time = time_slot.replace(hour=7, minute=0, second=0, microsecond=0)
        end_time = time_slot.replace(hour=20, minute=59, second=0, microsecond=0)
        
        # Check if time_slot is within the window
        return start_time <= time_slot <= end_time

    @schema_context(os.getenv('SCHEMA_NAME'))
    def get_accounts_to_be_reached_out_to_today(self, request, *args, **kwargs):
        
        # Get the start of yesterday's date
        yesterday = timezone.now().date() - timezone.timedelta(days=1)
        tomorrow = timezone.now().date() + timezone.timedelta(days=1)
        yesterday_start = timezone.make_aware(timezone.datetime.combine(yesterday, timezone.datetime.min.time()))
        unwanted_usernames = UnwantedAccount.objects.values_list('username', flat=True)

        # Filter accounts that are qualified and created from yesterday onwards, and exclude accounts that are not wanted
        accounts = Account.objects.filter(
            Q(qualified=True) & Q(created_at__gte=yesterday_start) & Q(created_at__lte=tomorrow)
        ).exclude(
            status__name="sent_compliment"
        ).exclude(
            igname__in=unwanted_usernames
        )
        return Response({'accounts': accounts.values('id','igname')},status=status.HTTP_200_OK)

    @schema_context(os.getenv('SCHEMA_NAME'))
    def get_qualified_threads_and_respond(self, request, *args, **kwargs):
        
        # Get the start of yesterday's date
        yesterday = timezone.now().date() - timezone.timedelta(days=1)
        tomorrow = timezone.now().date() + timezone.timedelta(days=1)
        yesterday_start = timezone.make_aware(timezone.datetime.combine(yesterday, timezone.datetime.min.time()))
        unwanted_usernames = UnwantedAccount.objects.values_list('username', flat=True)

        # Filter accounts that are qualified and created from yesterday onwards, and exclude accounts that are not wanted
        accounts = Account.objects.filter(
            Q(qualified=True) & Q(created_at__gte=yesterday_start) & Q(created_at__lte=tomorrow)
        ).exclude(
            status__name="sent_compliment"
        ).exclude(
            igname__in=unwanted_usernames
        ) 
        account_messages_sent = []
        
        if accounts.exists():
            for i,account in enumerate(accounts):
                    identifier = str(uuid.uuid4())
                    # combined_dict = {
                    #     identifier:account.igname
                    # }
                    # account_messages_sent.append(combined_dict)             
                    # if account.salesrep_set.exists(): # if they are assigned a salesrep
                    threads = Thread.objects.filter(account=account)  
                    if threads.exists():
                        for thread in threads:  
                            client_messages = Message.objects.filter(Q(thread__thread_id=thread.thread_id) & Q(sent_by="Client")).order_by("-sent_on")
                            robot_messages = Message.objects.filter(Q(thread__thread_id=thread.thread_id) & Q(sent_by="Robot")).order_by("-sent_on")
                            if client_messages.count() > 0 and robot_messages.count() == 0:
                                print("outbound sales")
                                # import pdb;pdb.set_trace()
                                time_slots = OutreachTime.objects.filter(time_slot__gte=timezone.now()).order_by('time_slot')
                                try:
                                    schedule = None
                                    # set a window to which it cannot by pass
                                    random_number = 1.5 + (2.5 - 1.5) * random.random()
                                    time_slot = timezone.now()+timezone.timedelta(hours=i/random_number)
                                    if self.is_time_slot_within_window(time_slot):
                                        send_first_compliment.apply_async(args=[[account.igname],thread.last_message_content], eta=time_slot,task_id=f"compliment_{account.id}_{time_slot.timestamp()}")
                                        try:
                                            account.outreach_time = time_slot
                                            account.save()
                                        except Exception as error:
                                            logging.warning(f"Failed to save outreach time - {error}")
                                    # run_scheduler.delay(target_time=time_slot,username=account.igname,message=thread.last_message_content)
                                        
                                        
                                    
                                    # send_first_compliment.delay(username=account.igname,message=thread.last_message_content)
                                except Exception as err:
                                    print(err)
                    else:
                        print("inbound sales")
                        # import pdb;pdb.set_trace()
                        time_slots = OutreachTime.objects.filter(time_slot__gte=timezone.now()).order_by('time_slot')
                        random_number = 1.5 + (2.5 - 1.5) * random.random()
                        try:
                            time_slot = timezone.now()+timezone.timedelta(hours=i/random_number)
                            # run_scheduler.delay(target_time=time_slot,username=account.igname,message="")
                            # time_slot = timezone.now()+timezone.timedelta(hours=i/2)
                            if self.is_time_slot_within_window(time_slot):
                                send_first_compliment.apply_async(args=[[account.igname],""], eta=time_slot,task_id=f"compliment_{account.id}_{time_slot.timestamp()}")

                                try:
                                    account.outreach_time = time_slot
                                    account.save()
                                except Exception as error:
                                    logging.warning(f"Failed to save outreach time - {error}")

                            # send_first_compliment.delay(username=account.igname,message="")
                            # send_first_compliment.delay(username=account.igname,message=thread.last_message_content)
                        except Exception as err:
                            print(err)
            return Response({'message':'succesfully scheduled reponses'},status=status.HTTP_200_OK)
        else:
            return Response({'message': 'accounts do not exist'})


    @schema_context(os.getenv('SCHEMA_NAME'))
    def generate_followup_response(self, request, *args, **kwargs):
        date_threshold = timezone.now() - timezone.timedelta(days=30)
        last_message_subquery = (
            Message.objects
            .filter(thread=OuterRef('thread'))
            .order_by('-sent_on')
        )
        latest_accounts_subquery = (
            Account.objects
            .filter(igname=OuterRef('igname'))  # Match the igname of the outer query
            .order_by('-created_at')  # Order by created_at descending
        )
        users_without_responses = (
            Account.objects
            .filter(
                qualified=True,
                question_asked=False,
                status__name='sent_compliment',
                created_at__gte=date_threshold  # Filter for accounts created in the last 30 days
            )
            .annotate(client_message_count=Count(
                'thread__message',
                filter=Q(thread__message__sent_by='Client')
            ))
            .annotate(last_message_sent_by_robot=Subquery(
                last_message_subquery.values('sent_by')[:1]  # Get the 'sent_by' field of the last message
            ))
            .filter(
                Q(client_message_count__gt=0) |  # Include users with client messages
                Q(last_message_sent_by_robot='Robot')  # Or where the last message was sent by Robot
            )
            .filter(
                created_at=Subquery(latest_accounts_subquery.values('created_at')[:1])  # Ensure we only get the latest account per igname
            )
            .values_list('igname', flat=True)
        )
        users_without_responses_list = list(users_without_responses)  # Convert queryset to list
        num_users = len(users_without_responses_list)
        random_users = None

        # If there are fewer than 10 users, slice accordingly
        if num_users > 10:
            random_users = random.sample(users_without_responses_list[:num_users - 10], min(3, num_users - 10))
        else:
            random_users = random.sample(users_without_responses_list, min(3, num_users))
        
        for username in random_users:
            account = Account.objects.filter(igname=username).latest('created_at')
            account.question_asked = True
            account.save()
            if account.thread_set.exists():
                thread = account.thread_set.latest('created_at')

                generate_response_endpoint = f"{os.getenv('API_URL')}/v1/instagram/dflow/{thread.thread_id}/generate-response/"
                
                try:
                    data = {"message": ""}
                    response = requests.post(generate_response_endpoint, json=data)  # Use json parameter for proper content-type
                    
                    if response.status_code in [200, 201]:
                        task_id = response.json()['task_id']
                        if task_id:
                            # Polling for task completion
                            celery_url = f"{os.getenv('API_URL')}/v1/instagram/celery-task-status/{task_id}/"
                            while True:
                                celery_response = requests.get(celery_url)

                                if celery_response.status_code == 200:
                                    print(f"Async Response: {celery_response.json()}")
                                    
                                    
                                    task_status = celery_response.json()['state']
                                    print(f"Status: {task_status}")
                                    if task_status == 'SUCCESS':
                                        message = celery_response.json()['result']['generated_comment']
                                        salesrep = SalesRep.objects.filter(available=True).latest('created_at')
                                        text_data = {
                                            "message": message,
                                            "username_to": account.igname,
                                            "username_from": salesrep.ig_username
                                        }
                                        text_response = requests.post(settings.MQTT_BASE_URL + "/send-message", json=text_data)
                                        if text_response.status_code == 200:
                                            print(f"Message sent to {account.igname}")
                                            time.sleep(100)  # Wait before sending the next message
                                        break  # Exit loop after successful message sending
                                    elif task_status == 'FAILURE':
                                        print(f"Task {task_id} failed.")
                                        break  # Exit loop on failure
                                else:
                                    print(f"Failed to get task status: {celery_response.status_code}")
                                
                                time.sleep(10)  # Wait before polling again (adjust as necessary)

                except Exception as err:
                    print(err)
            else:
                print(f"No thread found for {username}")

        return Response({"message": "Followup responses generated successfully"}, status=status.HTTP_200_OK)

    @schema_context(os.getenv('SCHEMA_NAME'))
    def generate_response(self, request, *args, **kwargs):
        thread = Thread.objects.filter(thread_id=kwargs.get('thread_id')).latest('created_at')
        req = request.data
        query = req.get("message")
        print(query)
        result = generate_response_automatic.delay(query, thread.thread_id)
        # import pdb;pdb.set_trace()
        print(result.id)

        return Response({
            "status": status.HTTP_200_OK,
            "message": "Task started successfully",
            "task_id": result.id
        }, status=status.HTTP_200_OK)


    @schema_context(os.getenv('SCHEMA_NAME'))
    def generate_response_v2(self, request, *args, **kwargs):
        req = request.data
        query = req.get("message")
        print(query)
        thread = Thread.objects.filter(thread_id=kwargs.get('thread_id')).latest('created_at')
        # thread = Thread.objects.filter(thread_id=thread_id).latest('created_at')
        account = Account.objects.filter(id=thread.account.id).latest('created_at')
        print(account.id)
        thread = Thread.objects.filter(account=account).latest('created_at')

        client_messages = query.split("#*eb4*#") if query else []
        # existing_messages = Message.objects.filter(thread=thread, content__in=client_messages)
        # if existing_messages.count() == len(client_messages):
        for client_message in client_messages:
            if client_message and not Message.objects.filter(content=client_message, sent_by="Client", thread=thread).exists():
                Message.objects.create(
                    content=client_message,
                    sent_by="Client",
                    sent_on=timezone.now(),
                    thread=thread
                )
            
        if client_messages:
            # if thread.last_message_content == client_messages[len(client_messages)-1]:
            #     return {
            #         "text": query,
            #         "success": True,
            #         "username": thread.account.igname,
            #         "generated_comment": "already_responded",
            #         "assigned_to": "Robot",
            #         "status":200
            #     }    
            
            
            thread.last_message_content = client_messages[len(client_messages)-1]
            thread.unread_message_count = len(client_messages)
            thread.last_message_at = timezone.now()
            thread.save()

        if thread.account.assigned_to == "Robot":
            try:
                gpt_resp = None
                last_message = thread.message_set.order_by('-sent_on').first()
                
                


                # if last_message.content and last_message.sent_by == "Robot":
                #     gpt_resp = "already_responded"
                # else:
                gpt_resp = get_gpt_response(account, str(client_messages), thread.thread_id)
                
                thread.last_message_content = gpt_resp
                thread.last_message_at = timezone.now()
                thread.save()

                result = gpt_resp
                
                Message.objects.create(
                    content=result,
                    sent_by="Robot",
                    sent_on=timezone.now(),
                    thread=thread
                )
                print(result)
                return Response({
                    "generated_comment": gpt_resp,
                    "text": query,
                    "success": True,
                    "username": thread.account.igname,
                    "assigned_to": "Robot",
                    "status": 200
                },status=200)

            except Exception as error:
                logging.warning(error)
                # send email
                try:
                    subject = f'Error in generate_response_automatic for {thread.account.igname}'
                    message = f'Error: {error}, this is in effort to debug what is wrong with consistent messaging'
                    from_email = 'lutherlunyamwi@gmail.com'
                    recipient_list = ['lutherlunyamwi@gmail.com','tomek@boostedchat.com']
                    send_mail(subject, message, from_email, recipient_list)
                except Exception as error:
                    print(error)

                return Response({
                    "error": str(error),
                    "success": False,
                    "username": thread.account.igname,
                    "assigned_to": "Robot",
                    "generated_comment": "Come again",
                    "status":500
                },status=500)

        elif thread.account.assigned_to == 'Human':
            return Response({
                "text": query,
                "success": True,
                "username": thread.account.igname,
                "generated_comment": "Come again",
                "assigned_to": "Human",
                "status": 200
            },status=200)
        # else:
        #         return {
        #             "text": query,
        #             "success": True,
        #             "username": thread.account.igname,
        #             "generated_comment": "already_responded",
        #             "assigned_to": "Robot",
        #             "status":200
        #         }
    
    def celery_task_status(self, request, task_id,*args,**kwargs):
        result = AsyncResult(task_id)
        print(result)
        
        return Response({
            'task_id': task_id,
            'state': result.state,
            'result': result.result if result.state == 'SUCCESS' else None,
        })


    @schema_context(os.getenv('SCHEMA_NAME'))
    def assign_operator(self, request, *args, **kwargs):
        try:
            thread = Thread.objects.filter(account__igname=kwargs.get('username')).latest('created_at')
            account = get_object_or_404(Account, id=thread.account.id)
            account.assigned_to = request.data.get("assigned_to") if request.data.get('assigned_to') else 'Human'
            account.save()
            try:
                subject = 'Hello Team'
                message = f'Please login to the system @https://booksy.us.boostedchat.com/ and respond to the following thread {account.igname}'
                from_email = 'lutherlunyamwi@gmail.com'
                recipient_list = ['lutherlunyamwi@gmail.com','tomek@boostedchat.com']
                send_mail(subject, message, from_email, recipient_list)
            except Exception as error:
                print(error)
        except Exception as error:
            print(error)


        return Response(
            {
                "status": status.HTTP_200_OK,
                "assign_operator": True
            }

        )

    
    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False, methods=["post"], url_path="save-external-messages")
    def save_external_messages(self, request, pk=None):
        
        account = None
        thread = None
        try:
            thread = Thread.objects.get(thread_id = request.data.get('thread_id'))
        except Thread.DoesNotExist:
            # create account object
            account = Account()
            account.igname = request.data.get('username')
            account.qualified = True
            account.save()

            # create thread object
            thread = Thread()
            thread.thread_id = request.data.get('thread_id')
            thread.account = account
            thread.save()

        # save message
        try:
            Message.objects.update_or_create(
                thread=thread,
                content=request.data.get("message"),
                sent_by="Client",
                sent_on=timezone.now()
            )
            return Response(
                {
                    "status": status.HTTP_200_OK,
                    "save": True
                }

            )
        except Exception as error:
            logging.warning(error)
            return Response(
                {
                    "status": status.HTTP_200_OK,
                    "save": False
                }

            )

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["get"], url_path="get-thread-messages")
    def get_thread_messages(self, request, pk=None):

        thread = self.get_object()
        messages = Message.objects.filter(thread=thread).order_by('sent_on')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["post"], url_path="delete-all-thread-messages")
    def delete_thread_messages(self, request, pk=None):

        thread = self.get_object()
        Message.objects.filter(thread=thread).delete()
        return Response({"message": "Messages deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    
    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["post"], url_path="reset-thread-count")
    def reset_thread_count(self, request, pk=None):

        thread = self.get_object()
        thread.unread_message_count = 0
        thread.save()
        return Response({"message": "OK"}, status=status.HTTP_204_NO_CONTENT)
    
    @schema_context(os.getenv('SCHEMA_NAME'))
    def messages_by_ig_thread_id(self, request, *args, **kwargs):
        # There come more than one threads with the same id
        # thread = Thread.objects.get(thread_id=kwargs.get('ig_thread_id'))
        thread = Thread.objects.filter(thread_id=kwargs.get('ig_thread_id')).first() 
        messages = Message.objects.filter(thread=thread).order_by('sent_on')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    @schema_context(os.getenv('SCHEMA_NAME'))
    def thread_by_ig_thread_id(self, request, *args, **kwargs):
        # There come more than one threads with the same id
        # thread = Thread.objects.get(thread_id=kwargs.get('ig_thread_id'))
        thread = Thread.objects.filter(thread_id=kwargs.get('ig_thread_id')).first() 
        serializer = SingleThreadSerializer(thread)

        return Response(serializer.data)

    
    @schema_context(os.getenv('SCHEMA_NAME'))
    def has_client_responded(self, request, *args, **kwargs):
        date_threshold = timezone.now() - timezone.timedelta(days=30)
        last_message_subquery = (
            Message.objects
            .filter(thread=OuterRef('thread'))
            .order_by('-sent_on')
        )
        latest_accounts_subquery = (
            Account.objects
            .filter(igname=OuterRef('igname'))  # Match the igname of the outer query
            .order_by('-created_at')  # Order by created_at descending
        )
        users_without_responses = (
            Account.objects
            .filter(
                qualified=True,
                question_asked=False,
                status__name='sent_compliment',
                created_at__gte=date_threshold  # Filter for accounts created in the last 30 days
            )
            .annotate(client_message_count=Count(
                'thread__message',
                filter=Q(thread__message__sent_by='Client')
            ))
            .annotate(last_message_sent_by_robot=Subquery(
                last_message_subquery.values('sent_by')[:1]  # Get the 'sent_by' field of the last message
            ))
            .filter(
                Q(client_message_count__gt=0) |  # Include users with client messages
                Q(last_message_sent_by_robot='Robot')  # Or where the last message was sent by Robot
            )
            .filter(
                created_at=Subquery(latest_accounts_subquery.values('created_at')[:1])  # Ensure we only get the latest account per igname
            )
            .values_list('igname', flat=True)
        )

        if len(users_without_responses) == 0:
            return Response({"has_responded":True}, status=status.HTTP_200_OK)
        elif len(users_without_responses) > 0:
            return Response({"has_responded":False}, status=status.HTTP_200_OK)
    

    @schema_context(os.getenv('SCHEMA_NAME'))
    def webhook(self,request,*args,**kwargs):
        data = None
        try:
            data = request.data
            print(data)
        except Exception as err:
            print(err)
            try:
                data = json.loads(request.body)
                print(data)
            except Exception as err:
                print(err)
                try:
                    data = request.json()
                except Exception as err:
                    print(err)
                    try:
                        data = json.loads(request.body.decode('utf-8'))
                    except  Exception as err:
                        print(err)
        
        try:
            closed = AccountsClosed()
            closed.data = data
            closed.save()
        except Exception as err:
            print(err,'was unable to save data')
                    
        return Response({"message":"webhook received"})
        

class Reschedule(APIView):
    def post(self, request, *args, **kwargs):
        reschedule.delay()

        print("Tasks have been scheduled successfully.")
    
        return Response({"message":"Tasks have been scheduled successfully."})



class MessageViewSet(viewsets.ModelViewSet):
    with schema_context(os.getenv('SCHEMA_NAME')):queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def get_serializer_class(self):
        return self.serializer_class

    @action(detail=True, methods=["delete"], url_path="delete-message")
    def delete_message(self, request, pk=None):

        message = self.get_object()
        message.delete()
        return Response({"message": "Message deleted successfully"}, status=status.HTTP_204_NO_CONTENT)






class CustomFieldListCreateView(generics.ListCreateAPIView):
    queryset = CustomField.objects.all()
    serializer_class = CustomFieldSerializer

class CustomFieldRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomField.objects.all()
    serializer_class = CustomFieldSerializer

# Custom Field Value API Views
class CustomFieldValueListCreateView(generics.ListCreateAPIView):
    queryset = CustomFieldValue.objects.all()
    serializer_class = CustomFieldValueSerializer

class CustomFieldValueRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomFieldValue.objects.all()
    serializer_class = CustomFieldValueSerializer

# Endpoint API Views
class EndpointListCreateView(generics.ListCreateAPIView):
    queryset = Endpoint.objects.all()
    serializer_class = EndpointSerializer

class EndpointRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Endpoint.objects.all()
    serializer_class = EndpointSerializer

# Connection API Views
class ConnectionListCreateView(generics.ListCreateAPIView):
    queryset = HttpOperatorConnectionModel.objects.all()
    serializer_class = HttpOperatorConnectionModelSerializer

class ConnectionRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = HttpOperatorConnectionModel.objects.all()
    serializer_class = HttpOperatorConnectionModelSerializer

# Workflow API Views
class WorkflowListCreateView(generics.ListCreateAPIView):
    queryset = WorkflowModel.objects.all()
    serializer_class = WorkflowModelSerializer

class WorkflowRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = WorkflowModel.objects.all()
    serializer_class = WorkflowModelSerializer

class WorkflowViewSet(viewsets.ModelViewSet):
    queryset = WorkflowModel.objects.all()
    serializer_class = WorkflowModelSerializer
    pagination_class = PaginationClass


class LoadInfoToDatabase(APIView):
    def get(self, request, *args, **kwargs):
        # Handle GET request
        return Response({'message': 'GET request handled'})

    def post(self,request):
        
        try:
            load_info_to_database()
            return Response({"success":True},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
# views.py
class MediaViewSet(viewsets.ModelViewSet):
    queryset = Media.objects.all()
    serializer_class = MediaSerializer
    
    @action(detail=True, methods=["post"], url_path="download-media")
    def download_media(self, request, pk=None):
        schema_name = os.getenv('SCHEMA_NAME', 'public')
        with schema_context(schema_name):
            try:
                # Handle missing scouts
                latest_available_scout = Scout.objects.filter(available=True).latest('created_at')
            except Scout.DoesNotExist:
                return Response(
                    {"error": "No available scouts found",
                     "message": "No available scouts found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            try:
                # Handle authentication failures
                client = login_user(latest_available_scout)
            except Exception as e:
                return Response(
                    {"error": f"Authentication failed: {str(e)}", "message": f"Authentication failed: {str(e)}"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            media_obj = self.get_object()
            try:
                media_id = client.media_pk_from_url(media_obj.media_url)
                media = client.media_info(media_id)
                if media_obj.media_type == "image":
                    media_obj.download_url = media.thumbnail_url.unicode_string() 
                elif media_obj.media_type == "video":
                    media_obj.download_url = media.video_url.unicode_string()
                media_obj.save()
                return Response(
                    {"download_url": media_obj.download_url},
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                return Response(
                    {"error": str(e), "message": str(e) },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            

class CustomFieldCreateView(CreateView):
    model = CustomField
    form_class = CustomFieldForm
    template_name = 'workflows/custom_field_form.html'
    success_url = reverse_lazy('custom_field_list')  # Redirect after creation


class CustomFieldUpdateView(UpdateView):
    model = CustomField
    form_class = CustomFieldForm
    template_name = 'workflows/custom_field_form.html'
    success_url = reverse_lazy('custom_field_list')  # Redirect after creation

class CustomFieldDeleteView(DeleteView):
    model = CustomField
    template_name = 'workflows/custom_field_confirm_delete.html'
    success_url = reverse_lazy('custom_field_list')  # Redirect after deletion

class CustomFieldListView(ListView):
    model = CustomField
    template_name = 'workflows/custom_field_list.html'
    context_object_name = 'custom_fields'

class CustomFieldValueCreateView(CreateView):
    model = CustomFieldValue
    form_class = CustomFieldValueForm
    template_name = 'workflows/custom_field_value_form.html'
    success_url = reverse_lazy('custom_field_list')  # Redirect after creation

    def form_valid(self, form):
        # Associate the custom field value with an endpoint (or other model)
        endpoint_id = self.kwargs['endpoint_id']
        endpoint = Endpoint.objects.get(id=endpoint_id)
        form.instance.content_object = endpoint  # Link to the endpoint
        # Create a JSON-like dictionary for saving
        field_name = form.cleaned_data['field'].name  # Get the name of the selected custom field
        field_value = form.cleaned_data['value']      # Get the input value
        
        # Constructing a dictionary to save as JSON
        json_value = {field_name: field_value}
        
        # Save the constructed JSON object in the value field
        form.instance.value = json_value
        return super().form_valid(form)


class EndpointListView(ListView):
    model = Endpoint
    template_name = 'workflows/endpoint_list.html'  # Template for listing endpoints
    context_object_name = 'endpoints'  # Variable name for the template context

class EndpointCreateView(CreateView):
    model = Endpoint
    form_class = EndpointForm
    template_name = 'workflows/endpoint_form.html'  # Template for creating an endpoint
    success_url = reverse_lazy('endpoint_list')  # Redirect URL after successful creation

class EndpointUpdateView(UpdateView):
    model = Endpoint
    form_class = EndpointForm
    template_name = 'workflows/endpoint_form.html'  # Template for updating an endpoint
    success_url = reverse_lazy('endpoint_list')  # Redirect URL after successful update

class EndpointDeleteView(DeleteView):
    model = Endpoint
    template_name = 'workflows/endpoint_confirm_delete.html'  # Template for confirming deletion
    success_url = reverse_lazy('endpoint_list')  # Redirect URL after successful deletion

class ConnectionListView(ListView):
    model = HttpOperatorConnectionModel
    template_name = 'workflows/connection_list.html'
    context_object_name = 'connections'

class ConnectionCreateView(CreateView):
    model = HttpOperatorConnectionModel
    form_class = HttpOperatorConnectionForm
    template_name = 'workflows/connection_form.html'
    success_url = reverse_lazy('connection_list')
    
    def form_valid(self, form):
        # Save the connection data to the database first
        connection = form.save()

        # Prepare data for Airflow API
        connection_data = {
            "connection_id": connection.connection_id,
            "conn_type": connection.conn_type,
            "host": connection.host,
            "port": connection.port,
            "login": connection.login,
            "password": connection.password,
            # Add other connection details as needed
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Replace with your actual Airflow base URL and credentials
        airflowcred = AirflowCreds.objects.latest('created_at')
        username = airflowcred.username
        password = airflowcred.password

        # Make a POST request to the Airflow API
        response = requests.post(
            f"{airflowcred.airflow_base_url}/api/v1/connections",
            data=json.dumps(connection_data),
            headers=headers,
            auth=HTTPBasicAuth(username, password),
        )

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            messages.success(self.request, "Connection successfully created in both Django and Airflow.")
        else:
            messages.error(self.request, f"Failed to create connection in Airflow: {response.text}")
        return super().form_valid(form)
    
class ConnectionUpdateView(UpdateView):
    model = HttpOperatorConnectionModel
    form_class = HttpOperatorConnectionForm
    template_name = 'workflows/connection_form.html'
    success_url = reverse_lazy('connection_list')

    def form_valid(self, form):
        # Save the connection data to the database first
        connection = form.save()

        # Prepare data for Airflow API
        connection_data = {
            "connection_id": connection.connection_id,
            "conn_type": connection.conn_type,
            "host": connection.host,
            "port": connection.port,
            "login": connection.login,
            "password": connection.password,
            # Add other connection details as needed
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Replace with your actual Airflow base URL and credentials
        airflowcred = AirflowCreds.objects.latest('created_at')
        username = airflowcred.username
        password = airflowcred.password

        # Make a PATCH request to the Airflow API
        response = requests.patch(
            f"{airflowcred.airflow_base_url}/api/v1/connections/{self.object.connection_id}",
            data=json.dumps(connection_data),
            headers=headers,
            auth=HTTPBasicAuth(username, password),
        )

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            messages.success(self.request, "Connection successfully updated in both Django and Airflow.")
        else:
            messages.error(self.request, f"Failed to update connection in Airflow: {response.text}")

        return super().form_valid(form)

class ConnectionDeleteView(DeleteView):
    model = HttpOperatorConnectionModel
    template_name = 'workflows/connection_confirm_delete.html'
    success_url = reverse_lazy('connection_list')

    def form_valid(self, form):
        # Save the connection data to the database first
        
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Replace with your actual Airflow base URL and credentials
        airflowcred = AirflowCreds.objects.latest('created_at')
        username = airflowcred.username
        password = airflowcred.password

        # Make a DELETE request to the Airflow API
        response = requests.delete(
            f"{airflowcred.airflow_base_url}/api/v1/connections/{self.object.connection_id}",
            headers=headers,
            auth=HTTPBasicAuth(username, password),
        )

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            messages.success(self.request, "Connection successfully deleted in both Django and Airflow.")
        else:
            messages.error(self.request, f"Failed to delete connection in Airflow: {response.text}")

        return super().form_valid(form)

class WorkflowInline():
    form_class = WorkflowModelForm
    model = WorkflowModel
    template_name = "workflows/workflow.html"

    # @schema_context("lunyamwi")
    def form_valid(self, form, schema_name=os.getenv('SCHEMA_NAME')):
        with schema_context(schema_name):
            named_formsets = self.get_named_formsets()
            if not all((x.is_valid() for x in named_formsets.values())):
                return self.render_to_response(self.get_context_data(form=form))
            print(self.object,'---object')
            is_update = self.object is not None
            self.object = form.save()
            if is_update:
                dag = self.object.dagmodel_set.latest('created_at')
                try:
                    airflowcreds = AirflowCreds.objects.latest('created_at')
                    headers = {
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    }
                    dag_update_data = {
                        "is_paused": False
                    }
                    resp = requests.patch(f"{airflowcreds.airflow_base_url}/api/v1/dags/{dag.dag_id}", 
                                          data=json.dumps(dag_update_data),
                                          auth=HTTPBasicAuth(airflowcreds.username, airflowcreds.password),
                                          headers=headers)
                    if resp.status_code == 200:
                        messages.success(self.request, f"DAG updated successfully {resp.status_code}")
                    else:
                        messages.error(self.request, f"Failed to update DAG: {resp.status_code}-{resp.text}")
                except Exception as e:
                    messages.error(self.request, f"Failed to update DAG: {str(e)}")
                print("Updating workflow:", self.object)
                # Additional logic for updating can go here
            else:
                print("Creating new workflow:", self.object)
                # Additional logic for creation can go here


            # for every formset, attempt to find a specific formset save function
            # otherwise, just save.
            for name, formset in named_formsets.items():
                formset_save_func = getattr(self, 'formset_{0}_valid'.format(name), None)
                if formset_save_func is not None:
                    formset_save_func(formset)
                else:
                    formset.save()
            generate_dag_script(self.object)
        return redirect('list_workflows')

    def formset_dags_valid(self, formset):
        """
        Hook for custom formset saving.. useful if you have multiple formsets
        """
        dags = formset.save(commit=False)  # self.save_formset(formset, contact)
        # add this, if you have can_delete=True parameter set in inlineformset_factory func
        for obj in formset.deleted_objects:
            obj.delete()
        for dag in dags:
            dag.workflow = self.object
            dag.save()

    def formset_httpoperators_valid(self, formset):
        """
        Hook for custom formset saving.. useful if you have multiple formsets
        """
        httpoperators = formset.save(commit=False)  # self.save_formset(formset, contact)
        # add this, if you have can_delete=True parameter set in inlineformset_factory func
        for obj in formset.deleted_objects:
            obj.delete()
        for operator in httpoperators:
            operator.dag = self.object.dagmodel_set.latest('created_at')
            operator.save()


class WorkflowCreate(WorkflowInline, CreateView):

    def get_context_data(self, **kwargs):
        ctx = super(WorkflowCreate, self).get_context_data(**kwargs)
        ctx['named_formsets'] = self.get_named_formsets()
        return ctx

    def get_named_formsets(self):
        if self.request.method == "GET":
            return {
                'dags': DagFormSet(prefix='dags'),
                'httpoperators': SimpleHttpOperatorFormSet(prefix='httpoperators'),
            }
        else:
            return {
                'dags': DagFormSet(self.request.POST or None, self.request.FILES or None, prefix='dags'),
                'httpoperators': SimpleHttpOperatorFormSet(self.request.POST or None, self.request.FILES or None, prefix='httpoperators'),
            }
        



    
class WorkflowUpdate(WorkflowInline, UpdateView):

    def get_context_data(self, **kwargs):
        ctx = super(WorkflowUpdate, self).get_context_data(**kwargs)
        ctx['named_formsets'] = self.get_named_formsets()
        return ctx

    def get_named_formsets(self):
        return {
            'dags': DagFormSet(self.request.POST or None, self.request.FILES or None, instance=self.object, prefix='dags'),
            'httpoperators': SimpleHttpOperatorFormSet(self.request.POST or None, self.request.FILES or None, instance=self.object.dagmodel_set.latest('created_at'), prefix='httpoperators'),
        }
    



class WorkflowRunner(DetailView):
    model = WorkflowModel
    template_name = "workflows/workflow_runner.html"
    context_object_name = "workflow"
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['workflow'] = self.object
        context['dag'] = self.object.dagmodel_set.latest('created_at')
        # Add the form to the context
        context['form'] = WorkflowRunnerForm()
        return context

    def post(self, request, *args, **kwargs):
        workflow = self.get_object()
        dag_id = workflow.dagmodel_set.latest('created_at').dag_id

        # Create an instance of the form with the POST data
        form = WorkflowRunnerForm(request.POST)
        
        if form.is_valid():
            # Process the form data (e.g., execute the workflow)
            push_to = form.cleaned_data['push_to']
            # You can add logic here based on the value of push_to
            if push_to == 'gcp':
                try:
                    push_file_gcp(filename=dag_id)
                    messages.success(request, "DAG file pushed to GCP successfully.")
                except Exception as e:
                    messages.error(request, f"Failed to push DAG file to GCP: {str(e)}")
            elif push_to == 'ssh':
                try:
                    push_file(filename=dag_id)
                    messages.success(request, "DAG file pushed to SSH successfully.")
                except Exception as e:
                    messages.error(request, f"Failed to push DAG file to SSH: {str(e)}")
            
            # Redirect after processing
            return redirect('workflow_runner', pk=workflow.pk)
        
        # If the form is not valid, re-render the page with the form errors
        return self.render_to_response(self.get_context_data(form=form))
    

class TriggerRun(View):
    
    def get(self, request, *args, **kwargs):
        
        workflow = WorkflowModel.objects.get(id=kwargs['pk'])
        dag_id = workflow.dagmodel_set.latest('created_at').dag_id
        try:
            airflowcreds = AirflowCreds.objects.latest('created_at')
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            dag_update_data = {
                "is_paused": False
            }
            resp = requests.patch(f"{airflowcreds.airflow_base_url}/api/v1/dags/{dag_id}", 
                                    data=json.dumps(dag_update_data),
                                    auth=HTTPBasicAuth(airflowcreds.username, airflowcreds.password),
                                    headers=headers)
            if resp.status_code in [200,201]:
                messages.success(request, "DAG unpaused successfully")
            else:
                messages.error(request, f"Failed to unpause DAG: {resp.text}")
        except Exception as err:
            messages.error(request, f"Failed to unpause DAG: {str(err)}")
        # Trigger the DAG run
        try:
            airflowcreds = AirflowCreds.objects.latest('created_at')
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            dag_run_data = {'conf': {}, 'dag_run_id': f'{dag_id}_{str(uuid.uuid4())}', 'note': None}
            resp = requests.post(
                f"{airflowcreds.airflow_base_url}/api/v1/dags/{dag_id}/dagRuns",
                data=json.dumps(dag_run_data),
                auth=HTTPBasicAuth(airflowcreds.username, airflowcreds.password),
                headers=headers
            )
            if resp.status_code == 200:
                messages.success(request, "DAG run triggered successfully.")
            else:
                messages.error(request, f"Failed to trigger DAG run: {resp.text}")
        except Exception as e:
            messages.error(request, f"Failed to trigger DAG run: {str(e)}")
        
        return redirect('list_workflows')
    

def delete_httpoperator(request, pk):
    try:
        httpOperator = SimpleHttpOperatorModel.objects.get(id=pk)
    except httpOperator.DoesNotExist:
        messages.success(
            request, 'Object Does not exit'
            )
        return redirect('update_workflow', pk=httpOperator.dag.workflow.id)

    httpOperator.delete()
    messages.success(
            request, 'httpOperator deleted successfully'
            )
    return redirect('update_workflow', pk=httpOperator.dag.workflow.id)


def delete_dag(request, pk):
    try:
        dag = DagModel.objects.get(id=pk)
    except dag.DoesNotExist:
        messages.success(
            request, 'Object Does not exit'
            )
        return redirect('update_workflow', pk=dag.workflow.id)

    dag.delete()
    messages.success(
            request, 'dag deleted successfully'
            )
    return redirect('update_workflow', pk=dag.workflow.id)


class WorkflowList(ListView):
    model = WorkflowModel
    template_name = "workflows/workflows.html"
    context_object_name = "workflows"
    
    with schema_context(os.getenv('SCHEMA_NAME')): queryset = WorkflowModel.objects.all()
    

    # @schema_context(os.getenv('SCHEMA_NAME'))
    def get_context_data(self, **kwargs):
        with schema_context(os.getenv('SCHEMA_NAME')):
            print(WorkflowModel.objects.count())
            # context = super().get_context_data(**kwargs)
            context = {}
            context['workflows'] = self.queryset
            print(WorkflowModel.objects.count())
            airflowcreds = AirflowCreds.objects.latest('created_at')
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            context['data'] = []
            try:
                print("Fetching DAGs from Airflow under construction")
                # resp = requests.get(f"{airflowcreds.airflow_base_url}/api/v1/dags", auth=HTTPBasicAuth(airflowcreds.username, airflowcreds.password),headers=headers)   
                # messages.success(self.request, "Fetched DAGs from Airflow successfully.")
                # if resp.status_code == 200:
                #     context['data'] = resp.json()
            except Exception as e:
                messages.error(self.request, f"Failed to fetch DAGs from Airflow: {str(e)}")

            # print(resp.json())
            return context



def display_workflows(request):
    with schema_context(os.getenv('SCHEMA_NAME')):
        workflows = WorkflowModel.objects.all()
        return render(request, 'workflows/workflows.html', {'workflows': workflows})



def generate_workflow(request):
    if request.method == 'POST':
        workflow_form = WorkflowModelForm(request.POST)
        simplehttpoperator_formset = SimpleHttpOperatorFormSet(request.POST)
        dag_formset = DagFormSet(request.POST)
        # import pdb;pdb.set_trace()
        if workflow_form.is_valid() and simplehttpoperator_formset.is_valid() and dag_formset.is_valid():
            workflow = workflow_form.save()
            simplehttpoperators = simplehttpoperator_formset.save()
            dags = dag_formset.save()
            workflow.simplehttpoperators.set(simplehttpoperators)
            for dag in dags:
                workflow.dag = dag  # WorkflowModel.dag is a foreign key
                workflow.save()
            generate_dag_script(workflow)
            return redirect("workflows")  # replace with your actual success page
        
    else:
        workflow_form = WorkflowModelForm()
        simplehttpoperator_formset = SimpleHttpOperatorFormSet(queryset=SimpleHttpOperatorModel.objects.none())
        dag_formset = DagFormSet(queryset=DagModel.objects.none())

    return render(request, 'workflows/workflow.html', {'workflow_form': workflow_form, 'simplehttpoperator_formset': simplehttpoperator_formset, 'dag_formset': dag_formset})






class InstagramLeadViewSet(viewsets.ModelViewSet):
    queryset = InstagramUser.objects.all()
    serializer_class = InstagramLeadSerializer
    pagination_class = PaginationClass

    @action(detail=False,methods=['post'],url_path='qualify-account')
    def qualify_account(self, request, pk=None):
        account = InstagramUser.objects.filter(username = request.data.get('username')).latest('created_at')
        accounts_qualified = []
        if account.info:
            account.qualified = request.data.get('qualify_flag')
            account.relevant_information = request.data.get("relevant_information")
            account.scraped = True
            account.save()
            accounts_qualified.append(
                {
                    "qualified":account.qualified,
                    "account_id":account.id
                }
            )
        else:
            return Response({"message":"user has not outsourced information"})
        
        return Response(accounts_qualified, status=status.HTTP_200_OK)

class ScoreViewSet(viewsets.ModelViewSet):
    queryset = Score.objects.all()
    serializer_class = ScoreSerializer

class QualificationAlgorithmViewSet(viewsets.ModelViewSet):
    queryset = QualificationAlgorithm.objects.all()
    serializer_class = QualificationAlgorithmSerializer

class SchedulerViewSet(viewsets.ModelViewSet):
    with schema_context(os.getenv('SCHEMA_NAME')):
        queryset = Scheduler.objects.all()
    serializer_class = SchedulerSerializer

class LeadSourceViewSet(viewsets.ModelViewSet):
    queryset = LeadSource.objects.all()
    serializer_class = LeadSourceSerializer


class SimpleHttpOperatorViewSet(viewsets.ModelViewSet):
    queryset = SimpleHttpOperatorModel.objects.all()
    serializer_class = SimpleHttpOperatorModelSerializer




    
class ScrapFollowers(APIView):
    def post(self, request):
        username = request.data.get("username")
        delay = int(request.data.get("delay"))
        round_ =  int(request.data.get("round"))
        chain = request.data.get("chain")
        if isinstance(username,list):
            for account in username:
                if chain:
                    scrap_followers(account,delay,round_=round_)
                else:
                    scrap_followers.delay(account,delay,round_=round_)
        else:
            scrap_followers.delay(username,delay,round_=round_)
        return Response({"success":True},status=status.HTTP_200_OK)

class ScrapTheCut(APIView):

    def post(self,request):
        chain = request.data.get("chain")
        round_ = request.data.get("round")
        index = request.data.get("index")
        record = request.data.get("record", None)
        refresh = request.data.get("refresh", False)
        number_of_leads = request.data.get("number_of_leads",0)
        try:
            users = None
            if refresh:
                scrap_the_cut(round_number=round_)
            if refresh and record:
                scrap_the_cut(round_number=round_,record=record)
            if not record:
                users = ScrappedData.objects.filter(round_number=round_)[index:index+number_of_leads]
            else:
                users = ScrappedData.objects.filter(round_number=round_)

            if users.exists():
                if chain:
                    for user in users:
                        scrap_users(list(user.response.get("keywords")[1]),round_ = round_,index=index)
                else:
                    for user in users:
                        scrap_users.delay(list(user.response.get("keywords")[1]),round_ = round_,index=index)

                return Response({"success": True}, status=status.HTTP_200_OK)
            else:
                logging.warning("Unable to find user")
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ScrapStyleseat(APIView):

    def post(self,request):
        region = request.data.get("region")
        category = request.data.get("category")
        chain = request.data.get("chain")
        round_ = request.data.get("round")
        index = request.data.get("index")
        try:
            subprocess.run(["scrapy", "crawl", "styleseat","-a",f"region={region}","-a",f"category={category}"])
            users = ScrappedData.objects.filter(inference_key=region)
            if users.exists():
                if chain:
                    for user in users:
                        scrap_users(list(user.response.get("businessName")),round_ = round_,index=index)
                else:
                    for user in users:
                        scrap_users.delay(list(user.response.get("businessName")),round_ = round_,index=index)

                return Response({"success": True}, status=status.HTTP_200_OK)
            else:
                logging.warning("Unable to find user")
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ScrapGmaps(APIView):

    def post(self,request):
        search_string = request.data.get("search_string")
        chain = request.data.get("chain")
        round_ = request.data.get("round")
        index = request.data.get("index")
        try:
            subprocess.run(["scrapy", "crawl", "gmaps","-a",f"search_string={search_string}"])
            users = ScrappedData.objects.filter(inference_key=search_string)
            if users.exists():
                if chain:
                    for user in users:
                        scrap_users(list(user.response.get("business_name")),round_ = round_,index=index)
                else:
                    for user in users:
                        scrap_users.delay(list(user.response.get("business_name")),round_ = round_,index=index)

                return Response({"success": True}, status=status.HTTP_200_OK)
            else:
                logging.warning("Unable to find user")
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class ScrapAPI(APIView):

    def get(self,request):
        try:
            # Execute Scrapy spider using the command line
            subprocess.run(["scrapy", "crawl", "api"])
            return Response({"success": True}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


class ScrapSitemaps(APIView):

    def get(self,request):
        try:
            # Execute Scrapy spider using the command line
            subprocess.run(["scrapy", "crawl", "sitemaps"])
            return Response({"success": True}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class ScrapMindBodyOnline(APIView):
    def get(self, request, *args, **kwargs):
        # Handle GET request
        return Response({'message': 'GET request handled'})

    def post(self,request):
        chain = request.data.get("chain")
        try:
            if chain:
                scrap_mbo()
            else:    
                # Execute Scrapy spider using the command line
                scrap_mbo.delay()
            return Response({"success": True}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ScrapURL(APIView):

    def get(self,request):
        try:
            # Execute Scrapy spider using the command line
            subprocess.run(["scrapy", "crawl", "webcrawler"])
            return Response({"success": True}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class ScrapUsers(APIView):
    def post(self,request):
        query = request.data.get("query")
        round_ = int(request.data.get("round"))
        index = int(request.data.get("index"))
        chain = request.data.get("chain")

        if isinstance(query,list):
            if chain:
                scrap_users(query,round_ = round_,index=index)
            else:
                scrap_users.delay(query,round_ = round_,index=index)
            
        return Response({"success":True},status=status.HTTP_200_OK)




class ScrapInfo(APIView):
    def post(self,request):
        
        delay_before_requests = 4
        delay_after_requests = 14
        step = 3
        accounts = 18
        round_number = 121
        chain = False
        if chain:
            scrap_info(delay_before_requests,delay_after_requests,step,accounts,round_number)
        else:
            scrap_info.delay(delay_before_requests,delay_after_requests,step,accounts,round_number)
        return Response({"success":True},status=status.HTTP_200_OK)
    


class ScrapMedia(APIView):
    def get(self, request, *args, **kwargs):
        # Handle GET request
        return Response({'message': 'GET request handled'})

    def post(self,request):
        try:
            media_links = request.data.get("media_links","")
            if media_links == "":
                scrap_media(media_links)
            elif len(media_links) > 0:
                scrap_media(ast.literal_eval(media_links))
            else:
                scrap_media()

        except Exception as err:
            print(err)
            scrap_media()
        return Response({"success":True},status=status.HTTP_200_OK)


class ScrapHashtag(APIView):
    def get(self, request, *args, **kwargs):
        # Handle GET request
        return Response({'message': 'GET request handled'})

    def post(self,request):
        hashtag = request.data.get("hashtag")
        try:
            scrap_hash_tag(hashtag)
        except Exception as e:
            scrap_hash_tag.delay(hashtag)
        return Response({"success":True},status=status.HTTP_200_OK)

class InsertAndEnrich(APIView):
    def post(self,request):
        keywords_to_check = request.data.get("keywords_to_check")
        round_ = request.data.get("round")
        chain = request.data.get("chain")
        if chain:
            insert_and_enrich(keywords_to_check,round_)
        else:
            insert_and_enrich.delay(keywords_to_check,round_)
        return Response({"success":True},status=status.HTTP_200_OK)
    

class GetMediaIds(APIView):
    def post(self,request):
        round_ = request.data.get("round")
        chain = request.data.get("chain")
        
        datasets = []
        for user in InstagramUser.objects.filter(Q(round=round_) & Q(qualified=True)):
            resp = requests.post(f"https://api.{os.environ.get('DOMAIN1', '')}.boostedchat.com/v1/instagram/has-client-responded/",data={"username":user.username})
            print(resp.status_code)
            if resp.status_code == 200:
                if resp.json()['has_responded']:
                    return Response({"message":"No need to carry on further because client has responded"}, status=status.HTTP_200_OK)
            else:
                resp = requests.get(f"https://api.{os.environ.get('DOMAIN1', '')}.boostedchat.com/v1/instagram/account/retrieve-salesrep/{user.username}/")
                if resp.status_code == 200:
                    print(resp.json())
                    dataset = {
                        "mediaIds": user.info.get("media_id"),
                        "username_from": resp.json()['salesrep'].get('username','')
                    }
                    datasets.append(dataset)
            

        if chain and round_:  
            return Response({"data": datasets},status=status.HTTP_200_OK)
        else:
            return Response({"error":"There is an error fetching medias"}, status=400)
        

class GetMediaComments(APIView):
    def post(self,request):
        round_ = request.data.get("round")
        chain = request.data.get("chain")
        
        datasets = []
        for user in InstagramUser.objects.filter(Q(round=round_) & Q(qualified=True)):
            resp = requests.post(f"https://api.{os.environ.get('DOMAIN1', '')}.boostedchat.com/v1/instagram/has-client-responded/",data={"username":user.username})
            print(resp.status_code)
            if resp.status_code == 200:
                if resp.json()['has_responded']:
                    return Response({"message":"No need to carry on further because client has responded"}, status=status.HTTP_200_OK)
            else:
                resp = requests.get(f"https://api.{os.environ.get('DOMAIN1', '')}.boostedchat.com/v1/instagram/account/retrieve-salesrep/{user.username}/")
                if resp.status_code == 200:
                    print(resp.json())
                    dataset = {
                        "mediaId": user.info.get("media_id"),
                        "comment": user.info.get("media_comment"),
                        "username_from": resp.json()['salesrep'].get('username','')
                    }
                    datasets.append(dataset)

        
        
        if chain and round_:  
            return Response({"data": datasets},status=status.HTTP_200_OK)
        else:
            return Response({"error":"There is an error fetching medias"}, status=400)
        
class GetAccounts(APIView):
    def post(self,request):
        round_ = request.data.get("round")
        chain = request.data.get("chain")
        
        datasets = []
        for user in InstagramUser.objects.filter(Q(round=round_) & Q(qualified=True)):
            resp = requests.post(f"https://api.{os.environ.get('DOMAIN1', '')}.boostedchat.com/v1/instagram/has-client-responded/",data={"username":user.username})
            print(resp.status_code)
            if resp.status_code == 200:
                if resp.json()['has_responded']:
                    return Response({"message":"No need to carry on further because client has responded"}, status=status.HTTP_200_OK)
            else:
                resp = requests.get(f"https://api.{os.environ.get('DOMAIN1', '')}.boostedchat.com/v1/instagram/account/retrieve-salesrep/{user.username}/")
                if resp.status_code == 200:
                    print(resp.json())
                    dataset = {
                        "mediaId": user.info.get("media_id"),
                        "comment": user.info.get("media_comment"),
                        "usernames_to": user.info.get("username"),
                        "username": user.info.get("username"),
                        "username_from": resp.json()['salesrep'].get('username','')
                    }
                    datasets.append(dataset)
        
        
        if chain and round_:  
            return Response({"data": datasets},status=status.HTTP_200_OK)
        else:
            return Response({"error":"There is an error fetching medias"}, status=400)
        


class FetchPendingInbox(APIView):
    def post(self, request):
        inbox_dataset = fetch_pending_inbox(session_id=request.data.get("session_id"))
        return Response({"data":inbox_dataset},status=status.HTTP_200_OK)
    
class ApproveRequest(APIView):
    def post(self, request):
        approved_datasets = approve_inbox_requests(session_id=request.data.get("session_id"))
        return Response({"data":approved_datasets},status=status.HTTP_200_OK)

class SendDirectAnswer(APIView):
    def post(self, request):
        send_direct_answer(session_id=request.data.get("session_id"),
                           thread_id=request.data.get("thread_id"),
                           message=request.data.get("message"))
        return Response({"success":True},status=status.HTTP_200_OK)
    

class PayloadQualifyingAgent(APIView):
    def post(self, request):
        yesterday = timezone.now().date() - timezone.timedelta(days=1)
        yesterday_start = timezone.make_aware(timezone.datetime.combine(yesterday, timezone.datetime.min.time()))

        # Filter accounts that are qualified and created from yesterday onwards
        round_ = request.data.get("round",1209)
        scrapped_users = InstagramUser.objects.filter(
            Q(created_at__gte=yesterday_start)).distinct('username')

        payloads = []
        for user in scrapped_users:
            payload = {
                "department":"Qualifying Department",
                "Scraped":{
                    "username":user.username,
                    "relevant_information":user.info,
                    "Relevant Information":user.info,
                    "outsourced_info":user.info
                }
            }
            payloads.append(payload)
        return Response({"data":payloads}, status=status.HTTP_200_OK)


class PayloadScrappingAgent(APIView):
    def post(self, request):
        payloads = []
        payload = {
            "department":"Scraping Department",
            "Start":{
                "mediaId":"",
                "comment":"",
                "number_of_leads":1,
                "relevant_information":{
                    "dummy":"dummy"
                },
                "Relevant Information":{
                    "dummy":"dummy"
                },
                "outsourced_info":{"dummy":"dummy"}
            }
        }

        payloads.append(payload)
        return Response({"data":payloads}, status=status.HTTP_200_OK)


class PayloadAssignmentAgent(APIView):
    def post(self, request):
        round_ = request.data.get("round",1209)
        yesterday = timezone.now().date() - timezone.timedelta(days=1)
        yesterday_start = timezone.make_aware(timezone.datetime.combine(yesterday, timezone.datetime.min.time()))

        qualified_users = InstagramUser.objects.filter(
            Q(created_at__gte=yesterday_start) & Q(qualified=True))
        payloads = []
        for user in qualified_users:
            payload =  {
                "department":"Assignment Department",
                "Qualified":{
                    "username":user.username,
                    "salesrep_capacity":2,
                    "Influencer":"",
                    "outsourced_info":user.info,
                    "relevant_Information":user.relevant_information,
                    "Relevant Information":user.relevant_information,
                    "relevant_information":user.relevant_information
                }
            }
            payloads.append(payload)
        return Response({"data":payloads}, status=status.HTTP_200_OK)




class GeneratePasswordEnc(APIView):
    def post(self, request, *args, **kwargs):
        password = request.data.get("password")
        cl = Client()
        return Response({
            "enc_pass":cl.password_encrypt(password)
        })




class ForceRecreateApi(APIView):
    def post(self, request):
        container_id = 'boostedchat-site-api-1'
        image_name = 'lunyamwimages/boostedchatapi-dev:staging'  # Match server tag

        try:
            client = docker.from_env()
            
            # Stop and remove existing container
            try:
                container = client.containers.get(container_id)
                container.stop()
                container.remove()
            except docker.errors.NotFound:
                pass  # Container already gone

            # Force pull fresh image with stream progress
            client.images.pull(image_name, stream=True, decode=True)
            
            
            # Create new container with correct image
            client.containers.run(
                image_name,
                detach=True,
                name=container_id,
                ports={'8000/tcp': 8000},
                volumes={'/var/run/docker.sock': {'bind': '/var/run/docker.sock', 'mode': 'rw'}},
                restart_policy={"Name": "always"}  # Add restart policy
            )

            return Response({"message": f"Container '{container_id}' recreated successfully."}, status=200)
            
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class ResolveCode(APIView):
    def post(self, request, *args, **kwargs):
        try:
            scout = Scout.objects.filter(username=request.data.get("username")).latest("created_at")
            scout.login_code = request.data.get("code")
            scout.save()
            return Response({"success":True,"code":scout.code},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        
        


class UpdatePassword(APIView):
    def post(self, request, *args, **kwargs):
        try:
            scout = Scout.objects.filter(username=request.data.get("username")).latest("created_at")
            scout.password_update = request.data.get("password")
            scout.save()
            return Response({"success":True, "password": scout.password_update}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)