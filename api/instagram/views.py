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
import backoff
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
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from django.conf import settings
from django.utils import timezone
from calendar import monthrange
from django.contrib import messages

from api.dialogflow.helpers.notify_click_up import notify_click_up_tech_notifications
from api.instagram.tasks import sales_rep_is_logged_in
from .tasks import scrap_followers,scrap_info,scrap_users,insert_and_enrich,scrap_mbo,scrap_media,load_info_to_database,scrap_hash_tag,fetch_all_followers_task
from api.helpers.dag_generator import generate_dag
from api.helpers.dag_file_handler import push_file,push_file_gcp
from api.helpers.date_helper import datetime_to_cron_expression
from api.scout.models import Scout
from boostedchatScrapper.spiders.helpers.thecut_scrapper import scrap_the_cut
from boostedchatScrapper.spiders.helpers.instagram_helper import fetch_pending_inbox,approve_inbox_requests,send_direct_answer
from django.db.models import Q
from django.utils.timezone import make_aware, now

from .models import ExperimentAssignee, InstagramUser
from django_tenants.utils import schema_context

from rest_framework import viewsets
from boostedchatScrapper.models import ScrappedData
from instagrapi import Client
import copy


from .models import (
    Score,
    QualificationAlgorithm,
    Scheduler, AirflowCreds,
    InstagramUser,
    LeadSource,
    DagModel,
    SimpleHttpOperatorModel,
    HttpOperatorConnectionModel,
    WorkflowModel,
    Endpoint,
    CustomField,
    CustomFieldValue,
    Media,
    Scout,
    Account,
    Comment,
    HashTag,
    Photo, Reel, Story, Thread, Video, Message,
    OutSourced,OutreachTime,AccountsClosed,Like,
    Comment,UnwantedAccount,StatusCheck, Experiment,
    ExperimentFieldDefinition, ExperimentStatus,
    ExperimentFieldValue
    )

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
    ExperimentAssigneeSerializer,
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
    ExperimentSerializer,
    ExperimentFieldDefinitionSerializer,
    ExperimentStatusSerializer,
    ExperimentFieldValueSerializer
)

from urllib.parse import urlparse
from auditlog.models import LogEntry
from celery.result import AsyncResult
from datetime import datetime, timedelta, time, timezone as timezone2
from dateutil.relativedelta import relativedelta
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


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


LUNYAMWI_INSTAGRAM_BASE_URL = os.getenv("LUNYAMWI_INSTAGRAM_BASE_URL", "")
LUNYAMWI_INSTAGRAM_API_KEY = os.getenv("LUNYAMWI_INSTAGRAM_API_KEY", "")

# Comment-related HikerAPI Views
class HikerCommentLikersChunkGql(APIView):
    """Get comment likers using GraphQL chunk method."""
    
    def post(self, request, *args, **kwargs):   
        """
        payload = {
            "comment_id": "18069481925141410"
        }
        """
        comment_id = request.data.get('comment_id')
        max_id = request.data.get('max_id')
        count = request.data.get('count', 12)
        
        if not comment_id:
            return Response({"error": "Comment ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if max_id:
                likers = cl.comment_likers_chunk_gql(comment_id, end_cursor=max_id)
            else:
                likers = cl.comment_likers_chunk_gql(comment_id)
            return Response({"likers": likers}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerCommentsChunkGql(APIView):
    """Get comments using GraphQL chunk method."""
    
    def post(self, request, *args, **kwargs):
        """
        payload = {
            "media_id": "321801234567
        }
        """
        media_id = request.data.get('media_id')
        max_id = request.data.get('max_id')
        
        if not media_id:
            return Response({"error": "Media ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if max_id:
                comments = cl.comments_chunk_gql(media_id, end_cursor=max_id)
            else:
                comments = cl.comments_chunk_gql(media_id)
            return Response({"comments": comments}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerCommentsThreadedChunkGql(APIView):
    """Get threaded comments using GraphQL chunk method."""
    
    def post(self, request, *args, **kwargs):
        media_id = request.data.get('media_id')
        comment_id = request.data.get('comment_id')
        max_id = request.data.get('max_id')
        
        if not media_id:
            return Response({"error": "Media ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if max_id:
                comments = cl.comments_threaded_chunk_gql(media_id, end_cursor=max_id)
            else:
                comments = cl.comments_threaded_chunk_gql(comment_id=comment_id, media_id=media_id)
            return Response({"comments": comments}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# Facebook Search HikerAPI Views
class HikerFbsearchAccountsV2(APIView):
    """Search accounts using Facebook search v2."""
    
    def post(self, request, *args, **kwargs):
        query = request.data.get('query')
        
        if not query:
            return Response({"error": "Search query is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            accounts = cl.fbsearch_accounts_v2(query)
            return Response({"accounts": accounts}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerFbsearchPlacesV1(APIView):
    """Search places using Facebook search v1."""
    
    def post(self, request, *args, **kwargs):
        query = request.data.get('query')
        
        
        if not query:
            return Response({"error": "Search query is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            places = cl.fbsearch_places_v1(query)
            return Response({"places": places}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerFbsearchPlacesV2(APIView):
    """Search places using Facebook search v2."""
    
    def post(self, request, *args, **kwargs):
        query = request.data.get('query')
        
        if not query:
            return Response({"error": "Search query is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            places = cl.fbsearch_places_v2(query)
            return Response({"places": places}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerFbsearchReelsV1(APIView):
    """Search reels using Facebook search v1."""

    def post(self, request, *args, **kwargs):
        query = request.data.get('query')

        if not query:
            return Response({"error": "Search query is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            reels = cl.fbsearch_reels_v1(query)
            return Response({"reels": reels}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerFbsearchReelsV2(APIView):
    """Search reels using Facebook search v2."""
    
    def post(self, request, *args, **kwargs):
        query = request.data.get('query')
        
        if not query:
            return Response({"error": "Search query is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            reels = cl.fbsearch_reels_v2(query)
            return Response({"reels": reels}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerFbsearchTopsearchHashtagsV1(APIView):
    """Search top hashtags using Facebook search v1."""
    
    def post(self, request, *args, **kwargs):
        query = request.data.get('query')
        
        if not query:
            return Response({"error": "Search query is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            hashtags = cl.fbsearch_topsearch_hashtags_v1(query)
            return Response({"hashtags": hashtags}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerFbsearchTopsearchV1(APIView):
    """Top search using Facebook search v1."""
    
    def post(self, request, *args, **kwargs):
        query = request.data.get('query')
        
        if not query:
            return Response({"error": "Search query is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            results = cl.fbsearch_topsearch_v1(query)
            return Response({"results": results}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerFbsearchTopsearchV2(APIView):
    """Top search using Facebook search v2."""
    
    def post(self, request, *args, **kwargs):
        query = request.data.get('query')
        
        if not query:
            return Response({"error": "Search query is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            results = cl.fbsearch_topsearch_v2(query)
            return Response({"results": results}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Hashtag HikerAPI Views
class HikerHashtagByNameV1(APIView):
    """Get hashtag information by name v1."""
    
    def post(self, request, *args, **kwargs):
        hashtag_name = request.data.get('hashtag_name')
        
        if not hashtag_name:
            return Response({"error": "Hashtag name is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            hashtag_info = cl.hashtag_by_name_v1(hashtag_name)
            return Response({"hashtag_info": hashtag_info}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerHashtagByNameV2(APIView):
    """Get hashtag information by name v2."""
    
    def post(self, request, *args, **kwargs):
        hashtag_name = request.data.get('hashtag_name')
        
        if not hashtag_name:
            return Response({"error": "Hashtag name is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            hashtag_info = cl.hashtag_by_name_v2(hashtag_name)
            return Response({"hashtag_info": hashtag_info}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class HikerHashtagMediasClipsChunkV1(APIView):
    """Get hashtag clips media in chunks v1."""
    
    def post(self, request, *args, **kwargs):
        hashtag_name = request.data.get('hashtag_name')
        max_id = request.data.get('max_id')
        
        if not hashtag_name:
            return Response({"error": "Hashtag name is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if max_id:
                clips = cl.hashtag_medias_clips_chunk_v1(hashtag_name, max_id=max_id)
            else:
                clips = cl.hashtag_medias_clips_chunk_v1(hashtag_name)
            return Response({"clips": clips}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerHashtagMediasClipsV1(APIView):
    """Get hashtag clips media v1."""
    
    def post(self, request, *args, **kwargs):
        hashtag_name = request.data.get('hashtag_name')
        amount = request.data.get('amount', 12)
        
        if not hashtag_name:
            return Response({"error": "Hashtag name is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if amount:
                clips = cl.hashtag_medias_clips_v1(hashtag_name, amount=amount)
            else:
                clips = cl.hashtag_medias_clips_v1(hashtag_name)
            return Response({"clips": clips}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerHashtagMediasClipsV2(APIView):
    """Get hashtag clips media v2."""
    
    def post(self, request, *args, **kwargs):
        hashtag_name = request.data.get('hashtag_name')
        page_id = request.data.get('page_id')
        
        if not hashtag_name:
            return Response({"error": "Hashtag name is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if page_id:
                clips = cl.hashtag_medias_clips_v2(hashtag_name, page_id=page_id)
            else:
                clips = cl.hashtag_medias_clips_v2(hashtag_name)
            return Response({"clips": clips}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class HikerHashtagMediasRecentV2(APIView):
    """Get hashtag recent media v2."""
    
    def post(self, request, *args, **kwargs):
        hashtag_name = request.data.get('hashtag_name')
        page_id = request.data.get('page_id')
        
        if not hashtag_name:
            return Response({"error": "Hashtag name is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if page_id:
                medias = cl.hashtag_medias_recent_v2(hashtag_name, page_id=page_id)
            else:
                medias = cl.hashtag_medias_recent_v2(hashtag_name)
            return Response({"medias": medias}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class HikerHashtagMediasTopChunkV1(APIView):
    """Get hashtag top media in chunks v1."""
    
    def post(self, request, *args, **kwargs):
        hashtag_name = request.data.get('hashtag_name')
        max_id = request.data.get('max_id')
        
        if not hashtag_name:
            return Response({"error": "Hashtag name is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if max_id:
                medias = cl.hashtag_medias_top_chunk_v1(hashtag_name, max_id=max_id)
            else:
                medias = cl.hashtag_medias_top_chunk_v1(hashtag_name)
            return Response({"medias": medias}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerHashtagMediasTopRecentChunkV1(APIView):
    """Get hashtag top recent media in chunks v1."""
    
    def post(self, request, *args, **kwargs):
        hashtag_name = request.data.get('hashtag_name')
        max_id = request.data.get('max_id')
        
        if not hashtag_name:
            return Response({"error": "Hashtag name is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if max_id:
                medias = cl.hashtag_medias_top_recent_chunk_v1(hashtag_name, max_id=max_id)
            else:
                medias = cl.hashtag_medias_top_recent_chunk_v1(hashtag_name)
            return Response({"medias": medias}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerHashtagMediasTopV1(APIView):
    """Get hashtag top media v1."""
    
    def post(self, request, *args, **kwargs):
        hashtag_name = request.data.get('hashtag_name')
        amount = request.data.get('amount', 12)
        
        if not hashtag_name:
            return Response({"error": "Hashtag name is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if amount:
                medias = cl.hashtag_medias_top_v1(hashtag_name, amount=amount)
            else:
                medias = cl.hashtag_medias_top_v1(hashtag_name)
            return Response({"medias": medias}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerHashtagMediasTopV2(APIView):
    """Get hashtag top media v2."""
    
    def post(self, request, *args, **kwargs):
        hashtag_name = request.data.get('hashtag_name')
        page_id = request.data.get('page_id')
        
        if not hashtag_name:
            return Response({"error": "Hashtag name is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if page_id:
                medias = cl.hashtag_medias_top_v2(hashtag_name, page_id=page_id)
            else:
                medias = cl.hashtag_medias_top_v2(hashtag_name)
            return Response({"medias": medias}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class HikerHighlightByIdV2(APIView):
    """Get highlight information by ID v2."""
    
    def post(self, request, *args, **kwargs):
        highlight_id = request.data.get('highlight_id')
        
        if not highlight_id:
            return Response({"error": "Highlight ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            highlight_info = cl.highlight_by_id_v2(highlight_id)
            return Response({"highlight_info": highlight_info}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerHighlightByUrlV1(APIView):
    """Get highlight information by URL v1."""
    
    def post(self, request, *args, **kwargs):
        highlight_url = request.data.get('highlight_url')
        
        if not highlight_url:
            return Response({"error": "Highlight URL is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            highlight_info = cl.highlight_by_url_v1(highlight_url)
            return Response({"highlight_info": highlight_info}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Location HikerAPI Views
class HikerLocationByIdV1(APIView):
    """Get location information by ID v1."""
    
    def post(self, request, *args, **kwargs):
        location_id = request.data.get('location_id')
        
        if not location_id:
            return Response({"error": "Location ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            location_info = cl.location_by_id_v1(location_id)
            return Response({"location_info": location_info}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerLocationGuidesV1(APIView):
    """Get location guides v1."""
    
    def post(self, request, *args, **kwargs):
        location_id = request.data.get('location_id')
        
        if not location_id:
            return Response({"error": "Location ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if location_id:
                guides = cl.location_guides_v1(location_id)
            
            return Response({"guides": guides}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerLocationMediasRecentChunkV1(APIView):
    """Get location recent media in chunks v1."""
    
    def post(self, request, *args, **kwargs):
        location_id = request.data.get('location_id')
        max_id = request.data.get('max_id')
        
        if not location_id:
            return Response({"error": "Location ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if max_id:
                medias = cl.location_medias_recent_chunk_v1(location_id, max_id=max_id)
            else:
                medias = cl.location_medias_recent_chunk_v1(location_id)
            return Response({"medias": medias}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerLocationMediasRecentV1(APIView):
    """Get location recent media v1."""
    
    def post(self, request, *args, **kwargs):
        location_id = request.data.get('location_id')
        amount = request.data.get('amount', 12)

        if not location_id:
            return Response({"error": "Location ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if amount:
                medias = cl.location_medias_recent_v1(location_id, amount=amount)
            else:
                medias = cl.location_medias_recent_v1(location_id)
            return Response({"medias": medias}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerLocationMediasTopChunkV1(APIView):
    """Get location top media in chunks v1."""
    
    def post(self, request, *args, **kwargs):
        location_id = request.data.get('location_id')
        max_id = request.data.get('max_id')
        
        if not location_id:
            return Response({"error": "Location ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if max_id:
                medias = cl.location_medias_top_chunk_v1(location_id, max_id=max_id)
            else:
                medias = cl.location_medias_top_chunk_v1(location_id)
            return Response({"medias": medias}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerLocationMediasTopV1(APIView):
    """Get location top media v1."""
    
    def post(self, request, *args, **kwargs):
        location_id = request.data.get('location_id')
        amount = request.data.get('amount', 12)
        
        if not location_id:
            return Response({"error": "Location ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if amount:
                medias = cl.location_medias_top_v1(location_id, amount=amount)
            else:
                medias = cl.location_medias_top_v1(location_id)
            return Response({"medias": medias}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerLocationSearchV1(APIView):
    """Search locations v1."""
    
    def post(self, request, *args, **kwargs):
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        
        if lat is None or lng is None:
            return Response({"error": "Search query is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            locations = cl.location_search_v1(lat=lat, lng=lng)
            return Response({"locations": locations}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Media HikerAPI Views
class HikerMediaByCodeV1(APIView):
    """Get media information by code v1."""
    
    def post(self, request, *args, **kwargs):
        media_code = request.data.get('media_code')
        
        if not media_code:
            return Response({"error": "Media code is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            media_info = cl.media_by_code_v1(media_code)
            return Response({"media_info": media_info}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerMediaByIdV1(APIView):
    """Get media information by ID v1."""
    
    def post(self, request, *args, **kwargs):
        media_id = request.data.get('media_id')
        
        if not media_id:
            return Response({"error": "Media ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            media_info = cl.media_by_id_v1(media_id)
            return Response({"media_info": media_info}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerMediaByUrlV1(APIView):
    """Get media information by URL v1."""
    
    def post(self, request, *args, **kwargs):
        media_url = request.data.get('media_url')
        
        if not media_url:
            return Response({"error": "Media URL is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            media_info = cl.media_by_url_v1(media_url)
            return Response({"media_info": media_info}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerMediaCodeFromPkV1(APIView):
    """Get media code from PK v1."""
    
    def post(self, request, *args, **kwargs):
        media_pk = request.data.get('media_pk')
        
        if not media_pk:
            return Response({"error": "Media PK is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            media_code = cl.media_code_from_pk_v1(media_pk)
            return Response({"media_code": media_code}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class HikerMediaCommentOffensiveV2(APIView):
    """Check if media comment is offensive v2."""
    
    def post(self, request, *args, **kwargs):
        media_id = request.data.get('media_id')
        comment_text = request.data.get('comment_text')
        
        if not comment_text:
            return Response({"error": "Comment text is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            result = cl.media_comment_offensive_v2(media_id=media_id, comment=comment_text)
            return Response({"result": result}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerMediaComments(APIView):
    """Get media comments."""
    
    def post(self, request, *args, **kwargs):
        media_id = request.data.get('media_id')
        count = request.data.get('count', 20)
        page_id = request.data.get('page_id')
        
        if not media_id:
            return Response({"error": "Media ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        
        try:
            if page_id:
                comments = cl.media_comments(media_id, count=count, page_id=page_id)
            else:
                comments = cl.media_comments(media_id, count=count)
            return Response({"comments": comments}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerMediaCommentsChunkV1(APIView):
    """Get media comments in chunks v1."""
    
    def post(self, request, *args, **kwargs):
        media_id = request.data.get('media_id')
        max_id = request.data.get('max_id')
        
        if not media_id:
            return Response({"error": "Media ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if max_id:
                comments = cl.media_comments_chunk_v1(media_id, max_id=max_id)
            else:
                comments = cl.media_comments_chunk_v1(media_id)
            return Response({"comments": comments}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerMediaCommentsV2(APIView):
    """Get media comments v2."""
    
    def post(self, request, *args, **kwargs):
        media_id = request.data.get('media_id')
        page_id = request.data.get('page_id')
        
        if not media_id:
            return Response({"error": "Media ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if page_id:
                comments = cl.media_comments_v2(media_id, page_id=page_id)
            else:
                comments = cl.media_comments_v2(media_id)
            return Response({"comments": comments}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerMediaInfoByCodeV2(APIView):
    """Get media info by code v2."""
    
    def post(self, request, *args, **kwargs):
        media_code = request.data.get('media_code')
        
        if not media_code:
            return Response({"error": "Media code is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            media_info = cl.media_info_by_code_v2(media_code)
            return Response({"media_info": media_info}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerMediaInfoByIdV2(APIView):
    """Get media info by ID v2."""
    
    def post(self, request, *args, **kwargs):
        media_id = request.data.get('media_id')
        
        if not media_id:
            return Response({"error": "Media ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            media_info = cl.media_info_by_id_v2(media_id)
            return Response({"media_info": media_info}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerMediaInfoByUrlV2(APIView):
    """Get media info by URL v2."""
    
    def post(self, request, *args, **kwargs):
        media_url = request.data.get('media_url')
        
        if not media_url:
            return Response({"error": "Media URL is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            media_info = cl.media_info_by_url_v2(media_url)
            return Response({"media_info": media_info}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerMediaInsightV1(APIView):
    """Get media insights v1."""
    
    def post(self, request, *args, **kwargs):
        media_id = request.data.get('media_id')
        
        if not media_id:
            return Response({"error": "Media ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            insights = cl.media_insight_v1(media_id)
            return Response({"insights": insights}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





# Media Likers HikerAPI Views (continued)
class HikerMediaLikersGql(APIView):
    """Get media likers using GraphQL."""
    
    def post(self, request, *args, **kwargs):
        media_id = request.data.get('media_id')
        
        if not media_id:
            return Response({"error": "Media ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            likers = cl.media_likers_gql(media_id)
            return Response({"likers": likers}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerMediaLikersV1(APIView):
    """Get media likers v1."""
    
    def post(self, request, *args, **kwargs):
        media_id = request.data.get('media_id')
        
        if not media_id:
            return Response({"error": "Media ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            likers = cl.media_likers_v1(media_id)
            return Response({"likers": likers}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerMediaLikersV2(APIView):
    """Get media likers v2."""
    
    def post(self, request, *args, **kwargs):
        media_id = request.data.get('media_id')
        
        if not media_id:
            return Response({"error": "Media ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            likers = cl.media_likers_v2(media_id)
            return Response({"likers": likers}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Media OEmbed and PK HikerAPI Views
class HikerMediaOembedV1(APIView):
    """Get media OEmbed v1."""
    
    def post(self, request, *args, **kwargs):
        media_url = request.data.get('media_url')
        
        if not media_url:
            return Response({"error": "Media URL is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            oembed = cl.media_oembed_v1(media_url)
            return Response({"oembed": oembed}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerMediaPkFromCodeV1(APIView):
    """Get media PK from code v1."""
    
    def post(self, request, *args, **kwargs):
        media_code = request.data.get('media_code')
        
        if not media_code:
            return Response({"error": "Media code is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            media_pk = cl.media_pk_from_code_v1(media_code)
            return Response({"media_pk": media_pk}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerMediaPkFromUrlV1(APIView):
    """Get media PK from URL v1."""
    
    def post(self, request, *args, **kwargs):
        media_url = request.data.get('media_url')
        
        if not media_url:
            return Response({"error": "Media URL is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            media_pk = cl.media_pk_from_url_v1(media_url)
            return Response({"media_pk": media_pk}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerMediaTemplateV2(APIView):
    """Get media template v2."""
    
    def post(self, request, *args, **kwargs):
        media_id = request.data.get('media_id')
        
        if not media_id:
            return Response({"error": "Media ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            template = cl.media_template_v2(media_id)
            return Response({"template": template}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerMediaUserV1(APIView):
    """Get media user v1."""
    
    def post(self, request, *args, **kwargs):
        media_id = request.data.get('media_id')
        
        if not media_id:
            return Response({"error": "Media ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            user = cl.media_user_v1(media_id)
            return Response({"user": user}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Save Media HikerAPI Views
class HikerSaveMedia(APIView):
    """Save media."""
    
    def post(self, request, *args, **kwargs):
        media_url = request.data.get('media_url')

        if not media_url:
            return Response({"error": "Media URL is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            result = cl.save_media(media_url)
            return Response({"result": result}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# Search HikerAPI Views
class HikerSearchAccountsV2(APIView):
    """Search accounts v2."""
    
    def post(self, request, *args, **kwargs):
        query = request.data.get('query')
        
        if not query:
            return Response({"error": "Search query is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            accounts = cl.search_accounts_v2(query)
            return Response({"accounts": accounts}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerSearchHashtagsV1(APIView):
    """Search hashtags v1."""
    
    def post(self, request, *args, **kwargs):
        query = request.data.get('query')
        
        if not query:
            return Response({"error": "Search query is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            hashtags = cl.search_hashtags_v1(query)
            return Response({"hashtags": hashtags}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerSearchHashtagsV2(APIView):
    """Search hashtags v2."""
    
    def post(self, request, *args, **kwargs):
        query = request.data.get('query')
        
        if not query:
            return Response({"error": "Search query is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            hashtags = cl.search_hashtags_v2(query)
            return Response({"hashtags": hashtags}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerSearchMusicV1(APIView):
    """Search music v1."""
    
    def post(self, request, *args, **kwargs):
        query = request.data.get('query')
        
        if not query:
            return Response({"error": "Search query is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            music = cl.search_music_v1(query)
            return Response({"music": music}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerSearchMusicV2(APIView):
    """Search music v2."""
    
    def post(self, request, *args, **kwargs):
        query = request.data.get('query')
        
        if not query:
            return Response({"error": "Search query is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            music = cl.search_music_v2(query)
            return Response({"music": music}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerSearchPlacesV2(APIView):
    """Search places v2."""
    
    def post(self, request, *args, **kwargs):
        query = request.data.get('query')
        
        if not query:
            return Response({"error": "Search query is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            places = cl.search_places_v2(query)
            return Response({"places": places}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerSearchReelsV2(APIView):
    """Search reels v2."""
    
    def post(self, request, *args, **kwargs):
        query = request.data.get('query')
        
        if not query:
            return Response({"error": "Search query is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            reels = cl.search_reels_v2(query)
            return Response({"reels": reels}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerSearchTopsearchV2(APIView):
    """Search top search v2."""
    
    def post(self, request, *args, **kwargs):
        query = request.data.get('query')
        
        if not query:
            return Response({"error": "Search query is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            results = cl.search_topsearch_v2(query)
            return Response({"results": results}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerSearchUsersV1(APIView):
    """Search users v1."""
    
    def post(self, request, *args, **kwargs):
        query = request.data.get('query')
        
        if not query:
            return Response({"error": "Search query is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            users = cl.search_users_v1(query)
            return Response({"users": users}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Share HikerAPI Views
class HikerShareByCodeV1(APIView):
    """Share by code v1."""
    
    def post(self, request, *args, **kwargs):
        media_code = request.data.get('media_code')
        
        if not media_code:
            return Response({"error": "Media code is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            result = cl.share_by_code_v1(media_code)
            return Response({"result": result}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerShareByUrlV1(APIView):
    """Share by URL v1."""
    
    def post(self, request, *args, **kwargs):
        media_url = request.data.get('media_url')
        
        if not media_url:
            return Response({"error": "Media URL is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            result = cl.share_by_url_v1(media_url)
            return Response({"result": result}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerShareReelByUrlV1(APIView):
    """Share reel by URL v1."""
    
    def post(self, request, *args, **kwargs):
        reel_url = request.data.get('reel_url')
        
        if not reel_url:
            return Response({"error": "Reel URL is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            result = cl.share_reel_by_url_v1(reel_url)
            return Response({"result": result}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Story HikerAPI Views
class HikerStoryByIdV1(APIView):
    """Get story by ID v1."""
    
    def post(self, request, *args, **kwargs):
        story_id = request.data.get('story_id')
        
        if not story_id:
            return Response({"error": "Story ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            story = cl.story_by_id_v1(story_id)
            return Response({"story": story}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerStoryByUrlV1(APIView):
    """Get story by URL v1."""
    
    def post(self, request, *args, **kwargs):
        story_url = request.data.get('story_url')
        
        if not story_url:
            return Response({"error": "Story URL is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            story = cl.story_by_url_v1(story_url)
            return Response({"story": story}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerStoryByUrlV2(APIView):
    """Get story by URL v2."""
    
    def post(self, request, *args, **kwargs):
        story_url = request.data.get('story_url')
        
        if not story_url:
            return Response({"error": "Story URL is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            story = cl.story_by_url_v2(story_url)
            return Response({"story": story}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerStoryDownloadByStoryUrlV1(APIView):
    """Download story by story URL v1."""
    
    def post(self, request, *args, **kwargs):
        story_url = request.data.get('story_url')
        
        if not story_url:
            return Response({"error": "Story URL is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            download_info = cl.story_download_by_story_url_v1(story_url)
            return Response({"download_info": download_info}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerStoryDownloadByUrlV1(APIView):
    """Download story by URL v1."""
    
    def post(self, request, *args, **kwargs):
        story_url = request.data.get('story_url')
        
        if not story_url:
            return Response({"error": "Story URL is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            download_info = cl.story_download_by_url_v1(story_url)
            return Response({"download_info": download_info}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerStoryDownloadV1(APIView):
    """Download story v1."""
    
    def post(self, request, *args, **kwargs):
        story_id = request.data.get('story_id')
        
        if not story_id:
            return Response({"error": "Story ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            download_info = cl.story_download_v1(story_id)
            return Response({"download_info": download_info}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Track HikerAPI Views

class HikerTrackByCanonicalIdV2(APIView):
    """Get track by canonical ID v2."""
    
    def post(self, request, *args, **kwargs):
        canonical_id = request.data.get('canonical_id')
        
        if not canonical_id:
            return Response({"error": "Canonical ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            track = cl.track_by_canonical_id_v2(canonical_id)
            return Response({"track": track}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerTrackByIdV2(APIView):
    """Get track by ID v2."""
    
    def post(self, request, *args, **kwargs):
        track_id = request.data.get('track_id')
        
        if not track_id:
            return Response({"error": "Track ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            track = cl.track_by_id_v2(track_id)
            return Response({"track": track}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class HikerTrackStreamByIdV2(APIView):
    """Get track stream by ID v2."""
    
    def post(self, request, *args, **kwargs):
        track_id = request.data.get('track_id')
        
        if not track_id:
            return Response({"error": "Track ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            track_stream = cl.track_stream_by_id_v2(track_id)
            return Response({"track_stream": track_stream}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# User HikerAPI Views
class HikerUserA2(APIView):
    """Get user A2 information."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            user_a2 = cl.user_a2(user_id)
            return Response({"user_a2": user_a2}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserAboutV1(APIView):
    """Get user about information v1."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            user_about = cl.user_about_v1(user_id)
            return Response({"user_about": user_about}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserByIdV1(APIView):
    """Get user by ID v1."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            user_info = cl.user_by_id_v1(user_id)
            return Response({"user_info": user_info}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserByIdV2(APIView):
    """Get user by ID v2."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            user_info = cl.user_by_id_v2(user_id)
            return Response({"user_info": user_info}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserByUrlV1(APIView):
    """Get user by URL v1."""
    
    def post(self, request, *args, **kwargs):
        user_url = request.data.get('user_url')
        
        if not user_url:
            return Response({"error": "User URL is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            user_info = cl.user_by_url_v1(user_url)
            return Response({"user_info": user_info}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserByUsernameV1(APIView):
    """Get user by username v1."""
    
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        
        if not username:
            return Response({"error": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            user_info = cl.user_by_username_v1(username)
            return Response({"user_info": user_info}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserByUsernameV2(APIView):
    """Get user by username v2."""
    
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        
        if not username:
            return Response({"error": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            user_info = cl.user_by_username_v2(username)
            return Response({"user_info": user_info}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class HikerUserClipsChunkV1(APIView):
    """Get user clips in chunks v1."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        max_id = request.data.get('max_id')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if max_id:
                clips = cl.user_clips_chunk_v1(user_id, end_cursor=max_id)
            else:
                clips = cl.user_clips_chunk_v1(user_id)
            return Response({"clips": clips}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class HikerUserClipsV2(APIView):
    """Get user clips v2."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        safe_int = request.data.get('safe_int', 12)
        page_id = request.data.get('page_id')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if page_id:
                clips = cl.user_clips_v2(user_id, safe_int=safe_int, page_id=page_id)
            else:
                clips = cl.user_clips_v2(user_id)
            return Response({"clips": clips}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserExploreBusinessesByIdV2(APIView):
    """Get user explore businesses by ID v2."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            businesses = cl.user_explore_businesses_by_id_v2(user_id)
            return Response({"businesses": businesses}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class HikerUserFollowersChunkGql(APIView):
    """Get user followers using GraphQL chunk method."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        end_cursor = request.data.get('end_cursor')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if end_cursor:
                followers = cl.user_followers_chunk_gql(user_id, end_cursor=end_cursor)
            else:
                followers = cl.user_followers_chunk_gql(user_id)
            return Response({"followers": followers}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserFollowersChunkV1(APIView):
    """Get user followers in chunks v1."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        max_id = request.data.get('max_id')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if max_id:
                followers = cl.user_followers_chunk_v1(user_id, max_id=max_id)
            else:
                followers = cl.user_followers_chunk_v1(user_id)
            return Response({"followers": followers}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserFollowersV2(APIView):
    """Get user followers v2."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        page_id = request.data.get('page_id')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if page_id:
                followers = cl.user_followers_v2(user_id, page_id=page_id)
            else:
                followers = cl.user_followers_v2(user_id)
            return Response({"followers": followers}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# User Following HikerAPI Views
class HikerUserFollowing(APIView):
    """Get user following."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        count = request.data.get('count', 20)
        page_id = request.data.get('page_id')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if page_id:
                following = cl.user_following(user_id, count=count, page_id=page_id)
            else:
                following = cl.user_following(user_id, count=count)
            return Response({"following": following}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserFollowingChunkGql(APIView):
    """Get user following using GraphQL chunk method."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        end_cursor = request.data.get('end_cursor')
        count = request.data.get('count', 20)
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if end_cursor:
                following = cl.user_following_chunk_gql(user_id, end_cursor=end_cursor)
            else:
                following = cl.user_following_chunk_gql(user_id)
            return Response({"following": following}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserFollowingChunkV1(APIView):
    """Get user following in chunks v1."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        max_id = request.data.get('max_id')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if max_id:
                following = cl.user_following_chunk_v1(user_id, max_id=max_id)
            else:
                following = cl.user_following_chunk_v1(user_id)
            return Response({"following": following}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserFollowingV2(APIView):
    """Get user following v2."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        count = request.data.get('count', 20)
        page_id = request.data.get('page_id')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if page_id:
                following = cl.user_following_v2(user_id, page_id=page_id)
            else:
                following = cl.user_following_v2(user_id)
            return Response({"following": following}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# User Highlights HikerAPI Views
class HikerUserHighlights(APIView):
    """Get user highlights."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            highlights = cl.user_highlights(user_id)
            return Response({"highlights": highlights}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class HikerUserHighlightsByUsernameV1(APIView):
    """Get user highlights by username v1."""
    
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        
        if not username:
            return Response({"error": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            highlights = cl.user_highlights_by_username_v1(username)
            return Response({"highlights": highlights}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserHighlightsByUsernameV2(APIView):
    """Get user highlights by username v2."""
    
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        
        if not username:
            return Response({"error": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            highlights = cl.user_highlights_by_username_v2(username)
            return Response({"highlights": highlights}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserHighlightsV1(APIView):
    """Get user highlights v1."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            highlights = cl.user_highlights_v1(user_id)
            return Response({"highlights": highlights}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserHighlightsV2(APIView):
    """Get user highlights v2."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            highlights = cl.user_highlights_v2(user_id)
            return Response({"highlights": highlights}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# User Medias HikerAPI Views
class HikerUserMedias(APIView):
    """Get user medias."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        count = request.data.get('count', 12)
        max_id = request.data.get('max_id')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if max_id:
                medias = cl.user_medias(user_id, count=count, max_id=max_id)
            else:
                medias = cl.user_medias(user_id, count=count)
            return Response({"medias": medias}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserMediasChunkV1(APIView):
    """Get user medias in chunks v1."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        end_cursor = request.data.get('end_cursor')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if end_cursor:
                medias = cl.user_medias_chunk_v1(user_id, end_cursor=end_cursor)
            else:
                medias = cl.user_medias_chunk_v1(user_id)
            return Response({"medias": medias}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserMediasPinnedV1(APIView):
    """Get user pinned medias v1."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        amount = request.data.get('amount', 12)
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            medias = cl.user_medias_pinned_v1(user_id, amount=amount)
            return Response({"medias": medias}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserMediasV2(APIView):
    """Get user medias v2."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        safe_int = request.data.get('safe_int', 12)
        page_id = request.data.get('page_id')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if page_id:
                medias = cl.user_medias_v2(user_id, safe_int=safe_int, page_id=page_id)
            else:
                medias = cl.user_medias_v2(user_id)
            return Response({"medias": medias}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# User Related Profiles and Search HikerAPI Views
class HikerUserRelatedProfilesGql(APIView):
    """Get user related profiles using GraphQL."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            related_profiles = cl.user_related_profiles_gql(user_id)
            return Response({"related_profiles": related_profiles}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserSearchFollowersV1(APIView):
    """Search user followers v1."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        query = request.data.get('query')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not query:
            return Response({"error": "Search query is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            followers = cl.user_search_followers_v1(user_id, query)
            return Response({"followers": followers}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserSearchFollowingV1(APIView):
    """Search user following v1."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        query = request.data.get('query')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not query:
            return Response({"error": "Search query is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            following = cl.user_search_following_v1(user_id, query)
            return Response({"following": following}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# User Stories HikerAPI Views
class HikerUserStoriesByUsernameV1(APIView):
    """Get user stories by username v1."""
    
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        
        if not username:
            return Response({"error": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            stories = cl.user_stories_by_username_v1(username)
            return Response({"stories": stories}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserStoriesByUsernameV2(APIView):
    """Get user stories by username v2."""
    
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        
        if not username:
            return Response({"error": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            stories = cl.user_stories_by_username_v2(username)
            return Response({"stories": stories}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserStoriesV1(APIView):
    """Get user stories v1."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            stories = cl.user_stories_v1(user_id)
            return Response({"stories": stories}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserStoriesV2(APIView):
    """Get user stories v2."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            stories = cl.user_stories_v2(user_id)
            return Response({"stories": stories}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class HikerUserTagMediasChunkV1(APIView):
    """Get user tag medias in chunks v1."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        max_id = request.data.get('max_id')
        
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if max_id:
                tag_medias = cl.user_tag_medias_chunk_v1(user_id, max_id=max_id)
            else:
                tag_medias = cl.user_tag_medias_chunk_v1(user_id)
            return Response({"tag_medias": tag_medias}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserTagMediasV2(APIView):
    """Get user tag medias v2."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        page_id = request.data.get('page_id')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            if page_id:
                tag_medias = cl.user_tag_medias_v2(user_id, page_id=page_id)
            else:
                tag_medias = cl.user_tag_medias_v2(user_id)
            return Response({"tag_medias": tag_medias}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# User Web Profile Info HikerAPI View
class HikerUserWebProfileInfoV1(APIView):
    """Get user web profile info v1."""
    
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        
        if not username:
            return Response({"error": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            profile_info = cl.user_web_profile_info_v1(username)
            return Response({"profile_info": profile_info}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# User Stream HikerAPI Views
class HikerUserstreamByIdV2(APIView):
    """Get user stream by ID v2."""
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            userstream = cl.userstream_by_id_v2(user_id)
            return Response({"userstream": userstream}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HikerUserstreamByUsernameV2(APIView):
    """Get user stream by username v2."""
    
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        
        if not username:
            return Response({"error": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            userstream = cl.userstream_by_username_v2(username)
            return Response({"userstream": userstream}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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


# In views.py - async version
class GetFollowersAsync(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        if not username:
            return Response({"error": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

        cl = initialize_hikerapi_client()
        try:
            user_info = cl.user_by_username_v1(username)
            if 'exc_type' in user_info:
                return Response({"error": f"User {username} not found"}, status=status.HTTP_404_NOT_FOUND)
            
            user_id = user_info.get('pk')
            
            # Start async task
            fetch_all_followers_task.delay(username, user_id)
            
            return Response({
                "message": "Follower fetching started",
                "status": "processing"
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetMediaLikers(APIView):
    # I want to work on this
    def post(self, request, *args, **kwargs):
        # Get the media ID from the request data
        media_links = request.data.get('media_links')
        if not media_links:
            return Response({"error": "Media Links is required."}, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(media_links, str):
            media_links = ast.literal_eval(media_links)

        # Initialize the HikerAPI client
        cl = initialize_hikerapi_client()
        likers_list = []
        influencers_list = ["vicblends","jrlusa","sly.huncho","robtheoriginal","barbersince98"]
        for link in media_links:
            if len(media_links) > 1:
                break
            try:
                # Fetch the likers of the media
                influencer = random.choice(influencers_list)
                logging.warning(f"influencer chosen ---->{influencer}")
                latest_influencer_media = cl.user_medias(user_id=cl.user_by_username_v1(username=influencer).get("pk"),count=1)[0]

                media_id = None
                use_media_links = request.data.get('use_media_links','')
                if use_media_links:
                    media_id = cl.media_pk_from_url_v1(link)
                else:
                    media_id = latest_influencer_media.get("pk")

                likers = cl.media_likers_v2(media_id)
                for i,liker in enumerate(likers['users']):
                    logging.warning(f"state: {i} out of {len(likers['users'])}")
                    check_user_exists = cl.user_by_username_v1(liker['username'])
                    if 'exc_type' in check_user_exists.keys():
                        continue
                    liker_data = {
                        "username": liker['username'],
                        "full_name": liker['full_name'],
                        "profile_pic_url": liker['profile_pic_url'],
                        "is_verified": liker['is_verified']
                    }
                    try:
                        InstagramUser.objects.create(
                            username=liker['username'],
                            info = cl.user_by_username_v1(liker['username'])
                        )
                    except Exception as e:
                        # Handle the case where the user already exists
                        print(f"User {liker.username} already exists in the database.")
                    
                    try:
                        account = Account.objects.create(
                            igname=liker['username'],
                            # ADD CHECK TO PRVENT BILLING JSONS FROM BEING SAVED
                            # {
                            #     "error": "Top up your account at https://hikerapi.com/billing",
                            #     "state": false,
                            #     "exc_type": "InsufficientFunds",
                            #     "media_id": null
                            # }
                            relevant_information=cl.user_by_username_v1(liker['username'])
                        )
                        user_media = cl.user_medias(user_id=cl.user_by_username_v1(username=liker['username']).get("pk"),count=1)[0]
                        OutSourced.objects.create(
                            results = {"media_id":user_media.get("id"),**cl.user_by_username_v1(liker['username'])},
                            account = account
                        )
                        logging.info(f"Account {liker['username']} created successfully.")
                    except Exception as e:
                        # Handle the case where the user already exists
                        print(f"account error --> {e}")
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

        if isinstance(media_links, str):
            media_links = ast.literal_eval(media_links)

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
                            info = cl.user_by_username_v1(commenter['user']['username'])
                        )
                    except Exception as e:
                        # Handle the case where the user already exists
                        print(f"Instagram user error: {e}")
                    
                    try:
                        account = Account.objects.create(
                            igname=commenter['username'],
                            relevant_information=cl.user_by_username_v1(commenter['user']['username'])
                        )
                        OutSourced.objects.create(
                            results = {"media_id":media_id,**cl.user_by_username_v1(commenter['user']['username'])},
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
    page_size = 200  # Set the number of items per page
    page_size_query_param = 'page_size'
    max_page_size = 200
    
class ReportPaginationClass(PageNumberPagination):
    page_size = 1000  # Set the number of items per page
    page_size_query_param = 'page_size'
    max_page_size = 1000

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
    report_pagination_class = ReportPaginationClass

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
            
            outsourced_info=Subquery(
                OutSourced.objects.filter(account=OuterRef('pk')).order_by('-created_at').values('results')[:1]
            ),
            # thread_id=Subquery(Thread.objects.filter(account=OuterRef('pk')).values('thread_id')[:1])
        ).order_by('-created_at')#order_by('-latest_message_at')

        # Filters from request
        search_query = request.GET.get("q")
        created_at_gte = request.GET.get("created_at_gte")
        created_at_lt = request.GET.get("created_at_lt")
        status_param = request.GET.get('status_param')
        outreach_success = request.GET.get('outreach_success')
        list_type = request.GET.get('list_type') 

        if search_query:
            queryset = queryset.filter(igname__icontains=search_query.strip())
        
        if status_param:
            if status_param.lower() == "null":
                queryset = queryset.filter(status_param__isnull=True)
            elif status_param.lower() == "blank":
                queryset = queryset.filter(status_param="")
            else:
                queryset = queryset.filter(status_param=status_param.strip())
     
                
        if outreach_success:
            if outreach_success.lower() == "true":
                queryset = queryset.filter(outreach_success=True)
                
            else:
                print("list_type----- this is what we are looking at ---->",list_type)
        
        # Date parsing
        created_filter = {}
        if created_at_gte:
            if list_type:
                if list_type.lower() == "outreach":
                    created_filter["created_at__gte"] = make_aware(datetime.strptime(created_at_gte, "%Y-%m-%d"))
                elif list_type.lower() == "won":
                    created_filter["won_date__range"] = (make_aware(datetime.strptime(created_at_gte, "%Y-%m-%d")), make_aware(datetime.strptime(created_at_lt, "%Y-%m-%d")) )
                elif list_type.lower() == "sales_qualified":
                    queryset = queryset.filter(
                        salesrep__isnull=False,
                        status_param='Sales Qualified',
                    )
                    created_filter["responded_date__range"] = (make_aware(datetime.strptime(created_at_gte, "%Y-%m-%d")), make_aware(datetime.strptime(created_at_lt, "%Y-%m-%d")) )
                elif list_type.lower() == "lost":
                    created_filter["lost_date__range"] = (make_aware(datetime.strptime(created_at_gte, "%Y-%m-%d")), make_aware(datetime.strptime(created_at_lt, "%Y-%m-%d")) )
                else:
                    print("created_at_gte----- this is what we are looking at ---->",created_at_gte)
                    created_filter["created_at__gte"] = make_aware(datetime.strptime(created_at_gte, "%Y-%m-%d"))
            else:
                created_filter["created_at__gte"] = make_aware(datetime.strptime(created_at_gte, "%Y-%m-%d"))

        if created_at_lt:
            if list_type is None:
              created_filter["created_at__lt"] = make_aware(datetime.strptime(created_at_lt, "%Y-%m-%d")) #+ timedelta(days=1)
        
            
        if created_filter:
            queryset = queryset.filter(**created_filter)
        
        # if list_type.lower() == "sales_qualified":
        #     queryset = queryset.filter(
        #         salesrep__isnull=False,
        #         status_param='Sales Qualified',
        #     )

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
    @action(detail=False, methods=['get'], url_path="weekly-reporting-details")
    def weekly_report_details_list(self, request, pk=None): 
        queryset = Account.objects.filter(salesrep__isnull=False)
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
            
            outsourced_info=Subquery(
                OutSourced.objects.filter(account=OuterRef('pk')).order_by('-created_at').values('results')[:1]
            ),
            # thread_id=Subquery(Thread.objects.filter(account=OuterRef('pk')).values('thread_id')[:1])
        ).order_by('id','-created_at')#order_by('-latest_message_at')

        # Filters from request
        search_query = request.GET.get("q")
        created_at_gte = request.GET.get("created_at_gte")
        created_at_lt = request.GET.get("created_at_lt")
        status_param = request.GET.get('status_param')
        outreach_success = request.GET.get('outreach_success')
        list_type = request.GET.get('list_type')
        
        if list_type is None:
             return Response({
            "count": 0,
            "next": "",
            "previous": "",
            "results": [],
            # "qualified": [],# AccountSerializer(qualified_accounts, many=True).data,
            "outreach_success": [],
            "scheduled": [],
            "total_outreach": 0,
            "total_scheduled": 0,
        })

        if search_query:
            queryset = queryset.filter(igname__icontains=search_query.strip()).distinct('id')
        
        # if status_param:
        #     if status_param.lower() == "null":
        #         queryset = queryset.filter(status_param__isnull=True)
        #     elif status_param.lower() == "blank":
        #         queryset = queryset.filter(status_param="")
        #     else:
        #         queryset = queryset.filter(status_param=status_param.strip())
        created_filter = {}
        if created_at_gte:
            created_filter["created_at__gte"] = make_aware(datetime.strptime(created_at_gte, "%Y-%m-%d"))
           
        if created_at_lt:
              created_filter["created_at__lt"] = make_aware(datetime.strptime(created_at_lt, "%Y-%m-%d")) #+ timedelta(days=1)
                
        if outreach_success:
            if outreach_success.lower() == "true":
                queryset = queryset.filter(outreach_success=True).distinct('id')
     
        start_date = make_aware(datetime.strptime(created_at_gte, "%Y-%m-%d"))
        end_date = make_aware(datetime.strptime(created_at_lt, "%Y-%m-%d") )
        match list_type.lower():    
            case "all":
                queryset = queryset.filter(
                    Q(outreach_time__date__range=(start_date, end_date)) |
                    Q(won_date__range=(start_date, end_date)) |
                    Q(lost_date__range=(start_date, end_date)) |
                    Q(sales_qualified_date__range=(start_date, end_date))
                ).distinct('id')
            case "sales_qualified":
                queryset = queryset.filter(
                        Q(status_param__iexact='sales qualified')| Q(status_param__iexact='Won'),
                        # created_at__gte=start_date, created_at__lt=end_date,
                        sales_qualified_date__gte=start_date, sales_qualified_date__lte=end_date
                    ).distinct('id')
            case "outreach":
                # queryset = queryset.filter(created_at__gte=start_date, created_at__lt=end_date).distinct('id')
                queryset = queryset.filter(outreach_time__gte=start_date,outreach_time__date__lte=end_date).distinct('id')
            case "won":
                queryset = queryset.filter(won_date__range=(start_date, end_date)).distinct('id')
            case "lost":
                queryset = queryset.filter(lost_date__range=(start_date, end_date)).distinct('id')
            case _:
                queryset.distinct('id')
                # Paginator for main list
        paginator = self.report_pagination_class()
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
        
        # Lets get from past three months to save loading time
        today = timezone.now()
        # three_months_ago = today - relativedelta(months=3)
        # start_of_week = three_months_ago - timedelta(days=three_months_ago.weekday())
        current_week = start_of_week 
        results = []

        while current_week < today:
            next_week = current_week + timedelta(days=7)
            end_of_week = next_week - timedelta(seconds=1)

            outreach_accounts = Account.objects.filter(
                # created_at__gte=current_week,
                # created_at__lte=end_of_week,
                outreach_time__gte=current_week,
                outreach_time__lt=end_of_week,
                outreach_success=True,
            ).distinct('id')
            outreach_count = outreach_accounts.count()
            
            print("Outrech count **",outreach_count)
            
            
            # thinking about putting instead of created_at sales_qualified_date__gte=start_date, sales_qualified_date__lt=end_date 
            sales_qualified_accounts = Account.objects.filter(
                sales_qualified_date__gte=current_week,
                sales_qualified_date__lte=end_of_week,
                salesrep__isnull=False,
            ).distinct('id')
            

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
                "week_end": next_week.strftime("%Y-%m-%d"),
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
            "results": results[::-1]
        })

    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=False, methods=['get'], url_path="monthly-reporting")
    def monthly_reporting(self, request):
        # Get January 1st of the current year with timezone
        tz = timezone.get_current_timezone()
        today = timezone.now()
        year = today.year
        current_month = 1 
        results = []

        while current_month <= today.month:
            # Get first day of the current month
            start_of_month = datetime(year, current_month, 1, tzinfo=tz)

            # Get last day of the current month
            last_day = monthrange(year, current_month)[1]
            end_of_month = datetime(year, current_month, last_day, 23, 59, 59, tzinfo=tz)

            outreach_accounts = Account.objects.filter(
                # created_at__gte=start_of_month,
                # created_at__lte=end_of_month,
                outreach_time__gte=start_of_month,
                outreach_time__date__lte=end_of_month,
                outreach_success=True,
            ).distinct('id')
            outreach_count = outreach_accounts.count()
            
            print("Outrech count **",outreach_count)
            
            sales_qualified_accounts = Account.objects.filter(
                Q(status_param__iexact='sales qualified')| Q(status_param__iexact='Won'),
                sales_qualified_date__gte=start_of_month,
                sales_qualified_date__lte=end_of_month,
                salesrep__isnull=False,
            ).distinct('id')
            

            responded_messages = Message.objects.filter(
                sent_by='Client',
                sent_on__gte=start_of_month,
                sent_on__lte=end_of_month
            ).values_list('thread__account__igname', flat=True).distinct()

            responded_count = responded_messages.count()
            responded_rate = round((responded_count / outreach_count) * 100,2) if outreach_count > 0 else 0
            
            call_scheduled_date = Account.objects.filter(call_scheduled_date__range=(start_of_month, end_of_month)).count()
            call_scheduled_rate = round((call_scheduled_date / outreach_count) * 100) if outreach_count > 0 else 0
            closing_date = Account.objects.filter(closing_date__range=(start_of_month, end_of_month)).count()
            closing_rate = round((closing_date / outreach_count) * 100,2) if outreach_count > 0 else 0
            won_date = Account.objects.filter(won_date__range=(start_of_month, end_of_month)).count()
            won_rate = round((won_date / outreach_count) * 100,2) if outreach_count > 0 else 0
            success_story_date = Account.objects.filter(success_story_date__range=(start_of_month, end_of_month)).count()
            success_story_rate = round((success_story_date / outreach_count) * 100,2) if outreach_count > 0 else 0
            lost_date = Account.objects.filter(lost_date__range=(start_of_month, end_of_month)).count()
            lost_rate = round((lost_date / outreach_count) * 100,2) if outreach_count > 0 else 0
            responded_date = Account.objects.filter(responded_date__range=(start_of_month, end_of_month)).count()
            sq_conversion_rate = round((sales_qualified_accounts.count()/outreach_count) * 100,2) if outreach_count > 0 else 0
            
           

            results.append({
                "week_start": start_of_month.strftime("%Y-%m-%d"),
                "week_end": end_of_month.strftime("%Y-%m-%d"),
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

            current_month += 1
        return Response({
            "results": results[::-1]
        })

    
    @schema_context(os.getenv('SCHEMA_NAME'))    
    @action(detail=False, methods=['get'], url_path="check-account-reached-out")
    def check_account_reached_out(self,request,*args,**kwargs):
        igname = request.query_params.get('username') 
        
        if not igname:
           return Response({"error": "username query param is required"}, status=400)
        
        # Check UnwantedAccount first
        if UnwantedAccount.objects.filter(username=igname).exists():
            return Response({"reached_out": True})
        
        # Then check Account
        account = Account.objects.filter(igname = igname)
        if account.exists():
            latest_account = account.latest('created_at')
            if latest_account.outreach_success or (
                 latest_account.status and latest_account.status.name == "sent_compliment"
            ):
                return Response({"reached_out":True})
        return Response({"reached_out":False})
        
    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=['post'], url_path="clear-convo")
    def clear_convo(self, request, **kwargs):
        account = self.get_object()
        
        try:
            # reset status
            UnwantedAccount.objects.filter(username=account.igname).delete()
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
        urls = []
        cl = login_user()

        for _, account in enumerate(self.queryset):
            try:
                url_info = cl.user_info_by_username(account.igname)
            except UserNotFound as err:
                logging.warning(err)

            account.competitor = urlparse(url_info.url).netloc
            account.save()
            url_info = {
                "url": url_info.url,
                "category": url_info.category,
                "competitor": account.competitor,
            }
            urls.append(url_info)
            status_code = status.HTTP_200_OK
            logging.warning(f"extracting info from => {account.igname}")

        response = {"actions": urls, "status_code": status_code}
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
    @action(detail=True, methods=["post"], url_path="sync-message")
    def sync_message(self, request, pk=None):
        thread_id = request.data.get("threadId")
        messages = request.data.get('messages')
        
        account = Account.objects.filter(thread__thread_id=thread_id)

        if account.exists():
            account = account.latest('created_at')
            account.assigned_to = 'Human' # NB: this is a temporary fix
            account.save()

        # TODO: take over conversations
        # else:
        #     account = Account.objects.create(igname='client')
        #     OutSourced.objects.create(results={"username": "client"}, account=account)
        try:


            thread_obj = Thread.objects.create(thread_id=thread_id)
            thread_obj.thread_id = thread_id
            thread_obj.account = account
            thread_obj.last_message_content = ""
            thread_obj.unread_message_count = 0
            thread_obj.last_message_at = datetime.now() # use UTC
            thread_obj.save()
            for message in  messages:
                
                message = Message()
                message.content = message.get("content")
                message.sent_by = "Robot"
                message.sent_on = datetime.fromtimestamp(int(message.get['timestamp'])/1000000) if message.get("timestamp") else datetime.now()
                message.thread = thread_obj
                message.save()
                print("message created then saved")
        except Exception as error:
            print(error)
            try:
                thread_obj = Thread.objects.filter(thread_id=thread_id).latest('created_at')
                thread_obj.thread_id = thread_id
                thread_obj.account = account
                thread_obj.last_message_content = ""
                thread_obj.unread_message_count = 0
                thread_obj.last_message_at = datetime.now() # use UTC
                thread_obj.save()
                for message in  messages:
                    message = Message()
                    message.content = message.get("content")
                    message.sent_by = "Robot"
                    message.sent_on = datetime.now()
                    message.thread = thread_obj
                    message.save()
                    print("message is saved")
            except Exception as error:
                print(error)
                print("message not saved")

        return Response({"success": True}, status=status.HTTP_201_CREATED)
    
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
                print("CREATED A NEW THREAD!")
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
        ).filter(dormant_profile_created=True)
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
                                print("inbound sales")
                                # import pdb;pdb.set_trace()
                                time_slots = OutreachTime.objects.filter(time_slot__gte=timezone.now()).order_by('time_slot')
                                try:
                                    schedule = None
                                    # set a window to which it cannot by pass
                                    random_number = 1.5 + (2.5 - 1.5) * random.random()
                                    time_slot = timezone.now()+timezone.timedelta(hours=i/random_number)
                                    if self.is_time_slot_within_window(time_slot):
                                        send_first_compliment.apply_async(args=[[account.igname],thread.last_message_content], eta=time_slot,task_id=f"compliment_{account.id}_{time_slot.timestamp()}")
                                        # try:
                                        #     account.outreach_time = time_slot
                                        #     account.save()
                                        # except Exception as error:
                                        #     logging.warning(f"Failed to save outreach time - {error}")
                                    # run_scheduler.delay(target_time=time_slot,username=account.igname,message=thread.last_message_content)
                                        
                                        
                                    
                                    # send_first_compliment.delay(username=account.igname,message=thread.last_message_content)
                                except Exception as err:
                                    print(err)
                    else:
                        print("outbound sales")
                        # import pdb;pdb.set_trace()
                        time_slots = OutreachTime.objects.filter(time_slot__gte=timezone.now()).order_by('time_slot')
                        random_number = 1.5 + (2.5 - 1.5) * random.random()
                        try:
                            time_slot = timezone.now()+timezone.timedelta(hours=i/random_number)
                            # run_scheduler.delay(target_time=time_slot,username=account.igname,message="")
                            # time_slot = timezone.now()+timezone.timedelta(hours=i/2)
                            if self.is_time_slot_within_window(time_slot):
                                send_first_compliment.apply_async(args=[[account.igname],""], eta=time_slot,task_id=f"compliment_{account.id}_{time_slot.timestamp()}")

                                # try:
                                #     account.outreach_time = time_slot
                                #     account.save()
                                # except Exception as error:
                                #     logging.warning(f"Failed to save outreach time - {error}")

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
    def generate_followup_response_v2(self, request, *args, **kwargs):
        account = Account.objects.to_follow_up()
        if not account:
            return Response({"message": "No accounts to follow up"}, status=status.HTTP_404_NOT_FOUND)
        # genereate a message based on the history or context if possible
        # generate_response = f"{os.getenv('API_URL')}/v1/instagram/dflow/{thread.thread_id}/generate-response/v2/"
        message = "I’ve just seen another barber getting their new clients and they reminded me of you -when is the right time to have a call to unlock your growth ?"
        salesrep = SalesRep.objects.filter(available=True).latest('created_at')
        text_data = {
            "message": message,
            "username_to": account.igname,
            "username_from": salesrep.ig_username
        }
        text_response = requests.post(settings.MQTT_BASE_URL + "/send-message", json=text_data)
        if "timestamp" in json.loads(text_response.text):
            print(f"Message sent to {account.igname}")
            account.follow_up_date = timezone.now().date()
            account.follow_up_count = account.follow_up_count + 1
            account.save()
            # send notification to the clickup
            notify_click_up_tech_notifications(comment_text=f"Follow up Message sent to ${account.igname}", notify_all=True)
        return Response({"message": "Followup responses generated successfully"}, status=status.HTTP_200_OK)
        # return Response(text_data, status=status.HTTP_200_OK)
    
    
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
                def should_retry_on_response(response):
                    # Retry on HTTP 401 or 403
                    return response is not None and json.loads(response.text).get(thread.account.salesrep_set.last().ig_username) == False

                @backoff.on_predicate(
                    backoff.constant,
                    predicate=should_retry_on_response,
                    interval=120,  # 120 seconds delay between retries
                    max_tries=3,
                    jitter=None  # no jitter for exact timing
                )
                def assert_if_salesrep_logged_in(salesrep):
                    # try:
                    # print(f"Sending message attempt for username: {username}")
                    json_data = json.dumps({"igname":salesrep})
                    response = requests.post(settings.MQTT_BASE_URL + "/accounts/isloggedin", data=json_data, headers={"Content-Type": "application/json"})
                    print(f"Response status code: {response.status_code}")

                    if json.loads(response.text).get(salesrep) == False: # if salesrep is not logged in
                        # Refresh login session on auth errors
                        notify_click_up_tech_notifications(
                            comment_text=f"Noticed the salesrep:{salesrep} is not logged in just before I responded therefore I shall retry relogin in 3 times with a 120 seconds interval",
                            notify_all=True
                        )
                        restart_payload = {"container_id": "boostedchat-site-mqtt-1"}  # restart the mqtt container
                        restart_mqtt = requests.post(f"{os.getenv('API_URL')}/serviceManager/restart-container/",data=restart_payload)
                                
                        if restart_mqtt.status_code == 200:
                            notify_click_up_tech_notifications(
                                comment_text=f"Received {restart_mqtt.status_code} - after trying to relogin the following salesrep:{salesrep} and now we can proceed on to sending the message",
                                notify_all=True
                            )
                            # Wait for 100 seconds to give the container time to restart
                            import time
                            time.sleep(100)
                    
                    return response
                    

                # Execute send with retries handled by backoff decorator
                # assert_if_salesrep_logged_in(thread.account.salesrep_set.last().ig_username)
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
                    # "generated_comment": "cool stuff!",
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
    def save_messages(self, request, pk=None):
        
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
        

class ExperimentViewSet(viewsets.ModelViewSet):
    with schema_context(os.getenv('SCHEMA_NAME')):
        queryset = Experiment.objects.all()
        pagination_class = PaginationClass
        serializer_class = ExperimentSerializer
        report_pagination_class = ReportPaginationClass
        
    @schema_context(os.getenv('SCHEMA_NAME'))
    def list(self, request, pk=None): 
        queryset = Experiment.objects.all()
        # Filters from request
        
        search_query = request.GET.get("name")
        start_at_gte = request.GET.get("start_gte")
        end_at_lt = request.GET.get("end_lt")
        primary_metric = request.GET.get('primary_metric')
        experiment_type = request.GET.get('experiment_type')
        experiment_status = request.GET.get('experiment_status')
        
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        
        if start_at_gte:
            formated_start_date = make_aware(datetime.strptime(start_at_gte, "%Y-%m-%d"))
            queryset = queryset.filter(start_date__gte=formated_start_date)
        
        if end_at_lt:
            formated_end_date = make_aware(datetime.strptime(end_at_lt, "%Y-%m-%d"))
            queryset = queryset.filter(end_date__lt=formated_end_date)
        
        if primary_metric:
            queryset = queryset.filter(primary_metric=primary_metric)
        
        if experiment_type:
            queryset = queryset.filter(experiment_type=experiment_type)

        if experiment_status:
            queryset = queryset.filter(status__name__iexact=experiment_status)
               
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
        
    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=["get"], url_path="experiment_fields")
    def get_field_definitions(self, request, pk=None):
        experiment_id = pk
        arr = []
        
        for exp_def in ExperimentFieldDefinition.objects.filter(experiment_id=experiment_id):
            serialized = ExperimentFieldDefinitionSerializer(exp_def)
            arr.append(serialized.data)
        return Response(arr)
    
    @schema_context(os.getenv('SCHEMA_NAME'))
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @schema_context(os.getenv('SCHEMA_NAME'))
    def perform_create(self, serializer):
        return super().perform_create(serializer)

    @schema_context(os.getenv('SCHEMA_NAME'))
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        try:
            
            print("Updating Experiment with data:")
            print(request.data)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as error:
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
          
    @schema_context(os.getenv('SCHEMA_NAME'))
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        try:
            original_experiment = self.get_object()
            new_name = f"{original_experiment.name}"
            count = Experiment.objects.filter(name=new_name).count()
            if count > 0:
                copy_number = count + 1
                new_name = f"{original_experiment.name} (Copy {copy_number})"
            
            new_experiment = copy.copy(original_experiment)
            new_experiment.pk = None  # Clear PK to create new object
            new_experiment.name = new_name
            new_experiment.version = f"EXP-{timezone.now().strftime('%m-%d-%Y@%H:%M:%S')}"
            new_experiment.save()
            # Map old definition IDs to new ones
            def_map = {}

            # Duplicate field definitions
            for field_def in original_experiment.field_definitions.all():
                new_def = copy.copy(field_def)
                new_def.pk = None
                new_def.experiment = new_experiment
                new_def.save()
                def_map[field_def.id] = new_def

            # Duplicate field values
            for value in original_experiment.field_values.all():
                if value.field_definition_id in def_map:
                    new_value = ExperimentFieldValue(
                        experiment=new_experiment,
                        field_definition=def_map[value.field_definition_id],
                        value=value.value,
                    )
                    new_value.save()
            serializer = self.get_serializer(new_experiment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Experiment.DoesNotExist:
            return Response({"error": "Original experiment not found."}, status=status.HTTP_404_NOT_FOUND)



class ExperimentStatusViewSet(viewsets.ModelViewSet):
    with schema_context(os.getenv('SCHEMA_NAME')):
        queryset = ExperimentStatus.objects.all()
        serializer_class = ExperimentStatusSerializer
        pagination_class = PaginationClass


    @schema_context(os.getenv('SCHEMA_NAME'))
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @schema_context(os.getenv('SCHEMA_NAME'))
    def perform_create(self, serializer):
        return super().perform_create(serializer)
    
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
        queryset = ExperimentStatus.objects.all()
        paginator = self.pagination_class()
        paginated_qs = paginator.paginate_queryset(queryset, request)
        serializer = self.get_serializer(paginated_qs, many=True)
        return Response({
            "count": paginator.page.paginator.count,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": serializer.data,
        })
    
class ExperimentAssigneeViewSet(viewsets.ModelViewSet):
    with schema_context(os.getenv('SCHEMA_NAME')):
        queryset = ExperimentAssignee.objects.all()
        serializer_class = ExperimentAssigneeSerializer
        pagination_class = PaginationClass


    @schema_context(os.getenv('SCHEMA_NAME'))
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @schema_context(os.getenv('SCHEMA_NAME'))
    def perform_create(self, serializer):
        return super().perform_create(serializer)
    
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
        queryset = ExperimentAssignee.objects.all()
        paginator = self.pagination_class()
        paginated_qs = paginator.paginate_queryset(queryset, request)
        serializer = self.get_serializer(paginated_qs, many=True)
        return Response({
            "count": paginator.page.paginator.count,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": serializer.data,
        })
     
    
class ExperimentFieldDefinitionViewSet(viewsets.ModelViewSet):
    with schema_context(os.getenv('SCHEMA_NAME')):
        queryset = ExperimentFieldDefinition.objects.all()
        serializer_class = ExperimentFieldDefinitionSerializer
    

    @schema_context(os.getenv('SCHEMA_NAME'))
    def create(self, request, *args, **kwargs):
        print("Creating ExperimentFieldValue with data:")
        print(request.data)
        # i need to create a field value here
        serializer = ExperimentFieldDefinitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        experiment_id = serializer.data['experiment']
        field_definition_id = serializer.data['id']
        experiment = Experiment.objects.get(id=experiment_id)
        field_definition = ExperimentFieldDefinition.objects.get(id=field_definition_id)
        ExperimentFieldValue.objects.create(experiment=experiment, 
                                            field_definition=field_definition,
                                            value=request.data['field_value'])
        return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
    
    @schema_context(os.getenv('SCHEMA_NAME'))
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            # get wont wokr here. we need to find not get
            field_value = ExperimentFieldValue.objects.filter(field_definition=instance).first()
            #if it does not exist, create it 
            if field_value:
                try:
                    field_value.value = request.data.get('field_value')
                    field_value.save()
                except Exception as error:
                    print("Error updating field value:")
                    print(error)
            else:
                field_value = ExperimentFieldValue.objects.create(
                    experiment=instance.experiment,
                    field_definition=instance,
                    value=request.data.get('field_value')
                )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as error:
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)

    
    @schema_context(os.getenv('SCHEMA_NAME'))
    def perform_create(self, serializer):
        return super().perform_create(serializer)
    
class ExperimentFieldValueViewSet(viewsets.ModelViewSet):
    with schema_context(os.getenv('SCHEMA_NAME')):
        queryset = ExperimentFieldValue.objects.all()
        serializer_class = ExperimentFieldValueSerializer
    

# class ExperimentFieldDefinitionViewSet(viewsets.ModelViewSet):
#     serializer_class = ExperimentFieldDefinitionSerializer

#     def get_queryset(self):
#         experiment_id = self.kwargs['experiment_pk']
#         return ExperimentFieldDefinition.objects.filter(experiment_id=experiment_id)

#     def perform_create(self, serializer):
#         experiment_id = self.kwargs['experiment_pk']
#         serializer.save(experiment_id=experiment_id)
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

                    try:
                        resp = requests.patch(f"{airflowcreds.airflow_base_url}/api/v1/dags/{dag.dag_id}", 
                                          data=json.dumps(dag_update_data),
                                          auth=HTTPBasicAuth(airflowcreds.username, airflowcreds.password),
                                          headers=headers,timeout=10)
                    except requests.exceptions.Timeout:
                        print("Request timed out")
                    except requests.exceptions.RequestException as e:
                        print(f"An error occurred: {e}")
                    
                    if resp.status_code == 200:
                        messages.success(self.request, f"DAG updated successfully {resp.status_code}")
                    else:
                        messages.error(self.request, f"Failed to update DAG: {resp.status_code}-{resp.text}")
                except Exception as e:
                    messages.error(self.request, f"Failed to update DAG: {str(e)}")
                print("Updating workflow:", self.object)
                logging.warning("updating workflow")
                # Additional logic for updating can go here
            else:
                print("Creating new workflow:", self.object)
                logging.warning("creating new workflow")
                # Additional logic for creation can go here


            # for every formset, attempt to find a specific formset save function
            # otherwise, just save.
            for name, formset in named_formsets.items():
                formset_save_func = getattr(self, 'formset_{0}_valid'.format(name), None)
                if formset_save_func is not None:
                    formset_save_func(formset)
                else:
                    formset.save()
            
            logging.warning(f"Workflow --> {self.object.id}")
            generate_dag_script.delay(self.object.id)
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





