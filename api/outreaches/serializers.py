from rest_framework import serializers
from django_celery_beat.models import PeriodicTask

# class PeriodicTaskSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PeriodicTask
#         # fields = '__all__'
#         fields = ['task']
class PeriodicTaskGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodicTask
        fields = '__all__'
class PeriodicTaskGetSerializer(serializers.ModelSerializer):
     class Meta:
        model = PeriodicTask
        fields = '__all__'
class PeriodicTaskPostSerializer(serializers.Serializer):
     task = serializers.ChoiceField(choices=["instagram.tasks.send_first_compliment"])
     startTime = serializers.IntegerField(default=14) #set to int
     startMinute = serializers.IntegerField(default=0) #set to int
     numperDay = serializers.IntegerField(default=30)#set to int
     user = serializers.CharField()
     salesrep = serializers.CharField(default="all")

class SingleTaskSerializer(serializers.Serializer):
     task = serializers.ChoiceField(choices=["instagram.tasks.send_first_compliment"])

class TaskBySalesRepSerializer(serializers.Serializer):
    task = serializers.ChoiceField(choices=["instagram.tasks.send_first_compliment"])
    sales_rep = serializers.CharField(required=True)
    status = serializers.ChoiceField(choices=["any", "enabled", "disabled"], default="any")
    order = serializers.ChoiceField(choices=[1,-1])
    number = serializers.IntegerField(default=-1)
    
class FirstComplimentSerializer(serializers.Serializer):
    task = serializers.ChoiceField(choices=["instagram.tasks.send_first_compliment"])
    user = serializers.CharField(required=True)

class IGFirstComplimentSerializer(serializers.Serializer):
    user = serializers.CharField(required=True)

class RescheduleBySalesRepSerializer(serializers.Serializer):
    task_name = serializers.ChoiceField(choices=["instagram.tasks.send_first_compliment"])
    sales_rep = serializers.CharField(required=True)
    start_hour = serializers.IntegerField(default=0)  # Assuming start_hour is an integer field
    start_minute = serializers.IntegerField(default=0)  # Assuming start_minute is an integer field
    # tasks_per_day = serializers.IntegerField(default=24)  # Assuming tasks_per_day is an integer field
    num_tasks = serializers.IntegerField(default=-1)  # Assuming tasks_per_day is an integer field

    def validate(self, data):
        """
        Validate the serializer data.
        """
        start_hour = data.get('start_hour')
        start_minute = data.get('start_minute')
        # tasks_per_day = data.get('tasks_per_day')

        if not (0 <= start_hour < 24):
            raise serializers.ValidationError("Start hour must be between 0 and 23.")
        
        if not (0 <= start_minute < 60):
            raise serializers.ValidationError("Start minute must be between 0 and 59.")
        
        # if tasks_per_day <= 0:
        #     raise serializers.ValidationError("Tasks per day must be greater than 0.")
        
        return data

class RescheduleAllSerializer(serializers.Serializer):
    task_name = serializers.ChoiceField(choices=["instagram.tasks.send_first_compliment"])
    start_hour = serializers.IntegerField(default=0)  # Assuming start_hour is an integer field
    start_minute = serializers.IntegerField(default=0)  # Assuming start_minute is an integer field
    # tasks_per_day = serializers.IntegerField(default=24)  # Assuming tasks_per_day is an integer field
    num_tasks = serializers.IntegerField(default=-1)  # Assuming tasks_per_day is an integer field

    def validate(self, data):
        """
        Validate the serializer data.
        """
        start_hour = data.get('start_hour')
        start_minute = data.get('start_minute')
        # tasks_per_day = data.get('tasks_per_day')

        if not (0 <= start_hour < 24):
            raise serializers.ValidationError("Start hour must be between 0 and 23.")
        
        if not (0 <= start_minute < 60):
            raise serializers.ValidationError("Start minute must be between 0 and 59.")
        
        # if tasks_per_day <= 0:
        #     raise serializers.ValidationError("Tasks per day must be greater than 0.")
        
        return data

class EnableBySalesRepSerializer(serializers.Serializer):
    salesrep = serializers.CharField(required=True)

    def validate(self, data):
        """
        Validate the serializer data.
        """
        salesrep = data.get('salesrep')

        if not salesrep:
            raise serializers.ValidationError("salesrep is required.")

        return data