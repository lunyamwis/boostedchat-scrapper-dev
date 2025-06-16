# serializers.py
import os
import json
import yaml
from datetime import timedelta
from rest_framework import serializers
from .models import Score, InstagramUser, QualificationAlgorithm, Scheduler, LeadSource,SimpleHttpOperatorModel,WorkflowModel,DagModel,Media,CustomField, CustomFieldValue, Endpoint, HttpOperatorConnectionModel, WorkflowModel,Account, Like, OutSourced, Comment, HashTag, Photo, Reel, Story, Thread, Video, Message, StatusCheck, OutSourced
from django.conf import settings
from django.db import IntegrityError
from api.helpers.dag_generator import generate_dag
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
            "statusParam"
            # "thread_id",
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
                        "sales_qualified_date": {"required": False, "allow_null": True}
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
            return to_camel_case(obj.status_param)

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

class CustomFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomField
        fields = '__all__'

class CustomFieldValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomFieldValue
        fields = '__all__'

class EndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Endpoint
        fields = '__all__'

class HttpOperatorConnectionModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = HttpOperatorConnectionModel
        fields = '__all__'

class WorkflowModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowModel
        fields = '__all__'
        
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

class DagModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DagModel
        fields = '__all__'
        extra_kwargs = {
            "id": {"required": False, "allow_null": True},
        }

class SimpleHttpOperatorModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimpleHttpOperatorModel
        fields = '__all__'
        extra_kwargs = {
            "id": {"required": False, "allow_null": True},
            "data": {"required": False, "allow_null": True},
        }

class WorkflowModelSerializer(serializers.ModelSerializer):
    simplehttpoperators = SimpleHttpOperatorModelSerializer(many=True, required=False)
    dag = DagModelSerializer(required=False)

    class Meta:
        model = WorkflowModel
        fields = ['id', 'name', 'simplehttpoperators','dag','delay_durations']
        extra_kwargs = {
            "id": {"required": False, "allow_null": True},
        }
    
    def create(self, validated_data):
        simplehttpoperators_data = validated_data.pop('simplehttpoperators', [])
        dag_data = validated_data.pop('dag', None)
        data = None

        workflow = super().create(validated_data)

        for simplehttpoperator_data in simplehttpoperators_data:
            if "urls" in simplehttpoperator_data:
                simplehttpoperator_data['urls'] = [json.dumps(urls_data) for urls_data in simplehttpoperator_data['urls']] 
            simplehttpoperator, _ = SimpleHttpOperatorModel.objects.get_or_create(**simplehttpoperator_data)
            workflow.simplehttpoperators.add(simplehttpoperator)

        if dag_data:
            dag, _ = DagModel.objects.get_or_create(**dag_data)
            workflow.dag = dag
            workflow.save()

        if "trigger_url" in dag_data:
        
            data = {
                "dag":[entry for entry in DagModel.objects.filter(id = workflow.dag.id).values()],
                "operators":[entry for entry in workflow.simplehttpoperators.values()],
                "data_seconds":workflow.delay_durations,
                "trigger_url":dag_data.get("trigger_url"),
                "trigger_url_expected_response":dag_data.get("trigger_url_expected_response")
            }
        else:
            data = {
                "dag":[entry for entry in DagModel.objects.filter(id = workflow.dag.id).values()],
                "operators":[entry for entry in workflow.simplehttpoperators.values()],
                "data_seconds":workflow.delay_durations
            }

        
        # Write the dictionary to a YAML file
        yaml_file_path = os.path.join(settings.BASE_DIR, 'api', 'helpers', 'include', 'dag_configs', f"{workflow.dag.dag_id}_config.yaml")
        with open(yaml_file_path, 'w') as yaml_file:
            try:
                yaml.dump(data, yaml_file, default_flow_style=False)
            except Exception as error:
                raise serializers.ValidationError(str(error))

        try:
            generate_dag()
        except Exception as error:
            raise serializers.ValidationError(str(error))

        return workflow


    
