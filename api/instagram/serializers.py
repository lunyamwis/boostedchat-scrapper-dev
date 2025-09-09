# serializers.py
import os
import json
import yaml
from datetime import timedelta
from rest_framework import serializers
from .models import ExperimentAssignee, Score, InstagramUser, QualificationAlgorithm, Scheduler, LeadSource,Account, Like, OutSourced, Comment, HashTag, Photo, Reel, Story, Thread, Video, Message, StatusCheck, OutSourced, Media
from .models import (
        Experiment, 
        ExperimentStatus, 
        ExperimentFieldDefinition,
        ExperimentFieldValue,
        ExperimentResult,
        ExperimentInput
    )
from django.conf import settings
from django.db import IntegrityError
from django_tenants.utils import schema_context
from django_celery_beat.models import PeriodicTask
import ast

def to_camel_case(snake_str):
    if snake_str is None:
        return None
    return ' '.join(word.capitalize() for word in snake_str.split())

# from rest_framework.utils.encoders import JSONEncoder
class OutSourcedSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutSourced
        fields = '__all__'
        extra_kwargs = {"id": {"required": False, "allow_null": True}}

class AccountSerializer(serializers.ModelSerializer):
    # account_history = serializers.CharField(source="history.latest",read_only=True)
    # print(account_history)
    # thread_id = serializers.SerializerMethodField()
    outsourced_info = serializers.SerializerMethodField()
    statusParam = serializers.SerializerMethodField()  # Capitalized output
    class Meta:
        model = Account
        fields = [
            "id",
            "igname",
            "full_name",
            "index",
            "is_manually_triggered",
            "relevant_information",
            "outreach_success",
            "qualified",
            "responded_date",
            "call_scheduled_date",
            "closing_date",
            "won_date",
            "success_story_date",
            "lost_date",
            "outreach_time",
            "notes",
            "created_at",
            "status_param",
            "outsourced_info",
            "sales_qualified_date",
            "statusParam",
            "assigned_to",
        ]
        extra_kwargs = {"id": {"required": False, "allow_null": True},
                        "index": {"required": False, "allow_null": True},
                        "is_manually_triggered": {"required": False, "allow_null": True},
                        "relevant_information": {"required": False, "allow_null": True},
                        "qualified": {"required": False, "allow_null": True},
                        "responded_date": {"required": False, "allow_null": True},
                        "call_scheduled_date": {"required": False, "allow_null": True},
                        "closing_date": {"required": False, "allow_null": True},
                        "won_date": {"required": False, "allow_null": True},
                        "success_story_date": {"required": False, "allow_null": True},
                        "lost_date": {"required": False, "allow_null": True},
                        "sales_qualified_date": {"required": False, "allow_null": True},
                        "outreach_success": {"required": False, "allow_null": True},
                        "assigned_to": {"required": False, "allow_null": True},
                        }
    # def get_thread_id(self, obj):
    #     # Get the first thread related to the account
    #     # thread = Thread.objects.filter(account=obj).first()
    #     # return thread.thread_id if thread else None
    #     return getattr(obj, 'thread_id', None) or \
    #         Thread.objects.filter(account=obj).values_list('thread_id', flat=True).first()
    def get_outsourced_info(self, obj):
        # The field will only be available if you annotated it
        return getattr(obj, "outsourced_info", None)
    def get_statusParam(self, obj):
        if obj.status_param:
            return obj.status_param.title()

class GetAccountSerializer(serializers.ModelSerializer):
    # status = serializers.CharField(source="account.status.name", read_only=True)
    class Meta:
        model = Account
        fields = '__all__'
        extra_kwargs = {
            "id": {"required": False, "allow_null": True},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            status_ = StatusCheck.objects.get(id=data['status'])
            data['status'] = status_.name
        except Exception as error:
            print(error)
        try:
            periodic_task = PeriodicTask.objects.get(name=f"SendFirstCompliment-{instance.igname}")
            data['outreach'] = periodic_task.crontab.human_readable 
        except PeriodicTask.DoesNotExist:
            pass
        return data
    
class ScheduleOutreachSerializer(serializers.Serializer):
    minute = serializers.CharField()
    hour = serializers.CharField()
    day_of_week = serializers.CharField()
    day_of_month = serializers.CharField()
    month_of_year = serializers.CharField()
    class Meta:
        fields = '__all__'

class GetSingleAccountSerializer(serializers.ModelSerializer):
    # status = serializers.CharField(source="account.status.name", read_only=True)
    class Meta:
        model = Account
        fields = '__all__'
        extra_kwargs = {
            "id": {"required": False, "allow_null": True},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            camelized_status_param = data['status_param'].title()
            data['status_param'] = camelized_status_param
        except Exception as error:
            pass
        try:
            status_ = StatusCheck.objects.get(id=data['status'])
            data['status'] = status_.name
        except Exception as error:
            print(error)

        try:
            outsourced_string = OutSourced.objects.get(account__id=data['id']).results
            data['outsourced'] = ast.literal_eval(outsourced_string)
        except Exception as error:
            data['outsourced'] = None
            print(error)
        try:
            periodic_task = PeriodicTask.objects.get(name=f"SendFirstCompliment-{instance.igname}")
            data['outreach'] = periodic_task.crontab.human_readable 
        except PeriodicTask.DoesNotExist:
            pass

        return data




class HashTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = HashTag
        fields = ["id", "hashtag_id"]
        extra_kwargs = {"id": {"required": False, "allow_null": True}}


class PhotoSerializer(serializers.ModelSerializer):
    account_username = serializers.CharField(source="account.igname", read_only=True)

    class Meta:
        model = Photo
        fields = ["id", "photo_id", "link", "name", "account_username"]
        extra_kwargs = {"id": {"required": False, "allow_null": True}}


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ["id", "video_id", "link", "name"]
        extra_kwargs = {"id": {"required": False, "allow_null": True}}


class ReelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reel
        fields = ["id", "reel_id", "link", "name"]
        extra_kwargs = {"id": {"required": False, "allow_null": True}}


class StorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Story
        fields = ["id", "link"]
        extra_kwargs = {"id": {"required": False, "allow_null": True}}


class UploadSerializer(serializers.Serializer):
    file_uploaded = serializers.FileField()

    class Meta:
        fields = ["file_uploaded"]


class AddContentSerializer(serializers.Serializer):
    assign_robot = serializers.BooleanField(default=True)
    approve = serializers.BooleanField(default=False)
    text = serializers.CharField(max_length=255, required=False)
    human_response = serializers.CharField(max_length=1024, required=False)
    generated_response = serializers.CharField(max_length=1024, required=False)


class SendManualMessageSerializer(serializers.Serializer):
    assigned_to = serializers.CharField(default="Robot")
    message = serializers.CharField(required=False)


class GenerateMessageInputSerializer(serializers.Serializer):
    thread_id = serializers.CharField(required=True)
    message = serializers.CharField(required=True)


class ThreadSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="account.igname", read_only=True)
    assigned_to = serializers.CharField(source="account.assigned_to", read_only=True)
    account_id = serializers.CharField(source="account.id", read_only=True)
    stage = serializers.CharField(source="account.index", read_only=True)
    
    class Meta:
        model = Thread
        fields = ["id", "username", "thread_id", "assigned_to", "account_id",
                  "unread_message_count", "last_message_content", "stage", "last_message_at",]
        extra_kwargs = {"id": {"required": False, "allow_null": True},
                        "account": {"required": False, "allow_null": True}}


    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            data['salesrep'] = instance.account.salesrep_set.last().ig_username
        except Exception as error:
            print(error)
        return data

class ThreadMessageSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField()

    class Meta:
        model = Thread
        fields = '__all__'

    def get_messages(self, obj):
        # Fetch and sort messages related to the thread by `sent_on` in descending order
        messages = obj.message_set.order_by('-sent_on')
        return MessageSerializer(messages, many=True).data

class SingleThreadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Thread
        fields = "__all__"


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = "__all__"
        extra_kwargs = {"id": {"required": False, "allow_null": True},
                        "sent_on": {"required": False, "allow_null": True}}   
        
        
class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'
        extra_kwargs = {"id": {"required": False, "allow_null": True}}     

class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = '__all__'
        extra_kwargs = {"id": {"required": False, "allow_null": True}}  


        
class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = '__all__'
        extra_kwargs = {
            "id": {"required": False, "allow_null": True},
        }

class InstagramLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstagramUser
        fields = '__all__'
        extra_kwargs = {
            "id": {"required": False, "allow_null": True},
        }
        
class ScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Score
        fields = '__all__'
        extra_kwargs = {
            "id": {"required": False, "allow_null": True},
            "linear_scale_capacity": {"required": False, "allow_null": True},
        }

class QualificationAlgorithmSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualificationAlgorithm
        fields = '__all__'
        extra_kwargs = {
            "id": {"required": False, "allow_null": True},
        }

class SchedulerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheduler
        fields = '__all__'
        extra_kwargs = {
            "id": {"required": False, "allow_null": True},
        }

class LeadSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadSource
        fields = '__all__'
        extra_kwargs = {
            "id": {"required": False, "allow_null": True},
            "account_usernames":{"required": False, "allow_null": True},
            "photo_links":{"required": False, "allow_null": True},
            "hashtags":{"required": False, "allow_null": True},
            "google_maps_search_keywords":{"required": False, "allow_null": True}
        }



    
class ExperimentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentStatus
        fields = ['id', 'name', 'description']
        extra_kwargs = {"id": {"required": False, "allow_null": True}}
        
class ExperimentAssigneeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentAssignee
        fields = ['id', 'name', 'description']
        extra_kwargs = {"id": {"required": False, "allow_null": True}}

class ExperimentSerializer(serializers.ModelSerializer):
    with schema_context(os.getenv('SCHEMA_NAME')):
        status = ExperimentStatusSerializer(read_only=True)
        status_id = serializers.PrimaryKeyRelatedField(
            queryset=ExperimentStatus.objects.all(), write_only=True, source='status'
        )
        field_definitions = serializers.SerializerMethodField()
        inputs = serializers.SerializerMethodField()
        experiment_results = serializers.SerializerMethodField()
        assignees = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=ExperimentAssignee.objects.all()
        )
        assignees_detail = ExperimentAssigneeSerializer(source='assignees', many=True, read_only=True)

    class Meta:
        model = Experiment
        fields = [
            'id', 
            'name', 
            'description', 
            'primary_metric', 
            'version',  
            'status_id', 
            'status',
            'start_date',
            'end_date',
            'actual_result',
            'expected_result',
            'hypothesis',
            'field_definitions',
            'inputs',
            'experiment_results',
            'assignees',
            'assignees_detail',
            'experiment_type'
        ]
        extra_kwargs = {"id": {"required": False, "allow_null": True},
                        "version": {"required": False, "allow_null": True},
                        "expected_result": {"required": False, "allow_null": True},
                        "actual_result": {"required": False, "allow_null": True},
                        "assigned_to": {"required": False, "allow_null": True},
                        "hypothesis": {"required": False, "allow_null": True},
                        "start_date": {"required": False, "allow_null": True},
                        "end_date": {"required": False, "allow_null": True},
                        "primary_metric": {"required": False, "allow_null": True},
                        "experiment_type": {"required": False, "allow_null": True}
                        }
    
    @schema_context(os.getenv('SCHEMA_NAME'))
    def get_field_definitions(self, obj):
        serializer = ExperimentFieldDefinitionSerializer(
            obj.field_definitions.all(),
            many=True,
            context={'experiment_id': obj.id}
        )
        return serializer.data

    @schema_context(os.getenv('SCHEMA_NAME'))
    def get_inputs(self, obj):
        serializer = ExperimentInputSerializer(
            obj.inputs.select_related('field').all(),
            many=True
        )
        return serializer.data
    
    @schema_context(os.getenv('SCHEMA_NAME'))
    def get_experiment_results(self, obj):
        results_qs = ExperimentResult.objects.filter(experiment=obj)
        return ExperimentResultSerializer(results_qs, many=True).data
        

class ExperimentFieldDefinitionSerializer(serializers.ModelSerializer):
    
    field_value = serializers.SerializerMethodField()
    class Meta:
        model = ExperimentFieldDefinition
        fields = ['id', 'experiment', 'config', 'is_experiment_input', 'is_metric_field', 'is_result_field', 'value', 'field_value']
        extra_kwargs = {"id": {"required": False, "allow_null": True}}

    def validate(self, data):
        if data.get('is_experiment_input') == True and  data.get('is_result_field') == True:
            raise serializers.ValidationError(
                "Either one of 'is_experiment_input' or 'is_result_field' can be True."
            )
        return data
    
    @schema_context(os.getenv('SCHEMA_NAME'))
    def get_field_value(self, obj):
        serializer = ExperimentFieldValueSerializer(
            obj.field_values.filter(field_definition_id=obj.id).first(),
        )
        return serializer.data.get('value')
    

class ExperimentFieldValueSerializer(serializers.ModelSerializer):
    with schema_context(os.getenv('SCHEMA_NAME')):
        field_definition_id = serializers.PrimaryKeyRelatedField(
            queryset=ExperimentFieldDefinition.objects.all(),
            source='field_definition',
            write_only=True
        )
        field_definition = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ExperimentFieldValue
        fields = ['id', 'experiment', 'field_definition_id', 'field_definition', 'value']
        read_only_fields = ['id', 'experiment', 'field_definition']

    
    @schema_context(os.getenv('SCHEMA_NAME'))
    def get_field_definition(self, obj):
        return {
            "id": obj.field_definition.id,
            "config": obj.field_definition.config,
            "is_experiment_input": obj.field_definition.is_experiment_input,
            "is_result_field": obj.field_definition.is_result_field,
            "is_metric_field": obj.field_definition.is_metric_field,
        }

    @schema_context(os.getenv('SCHEMA_NAME'))
    def create(self, validated_data):
        experiment = self.context['experiment']
        return ExperimentFieldValue.objects.create(experiment=experiment, **validated_data)
    
# class ExperimentFieldValueSerializer(serializers.ModelSerializer):
#     with schema_context(os.getenv('SCHEMA_NAME')):
#         field_definition = ExperimentFieldDefinition()

#     class Meta:
#         model = ExperimentFieldValue
#         fields = ['field_definition', 'value']
        
class ExperimentResultSerializer(serializers.ModelSerializer):
    with schema_context(os.getenv('SCHEMA_NAME')):
        field_definition = ExperimentFieldDefinition()

    class Meta:
        model = ExperimentResult
        fields = ['field_definition', 'value']


class ExperimentInputSerializer(serializers.ModelSerializer):
    with schema_context(os.getenv('SCHEMA_NAME')):
        field = ExperimentFieldDefinition()

    class Meta:
        model = ExperimentInput
        fields = ['field', 'value']