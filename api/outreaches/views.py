# dev1
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_GET
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json
import os
import ast
from django.shortcuts import render
from rest_framework import viewsets
from .serializers import PeriodicTaskGetSerializer
from .serializers import PeriodicTaskPostSerializer, TaskBySalesRepSerializer, FirstComplimentSerializer, SingleTaskSerializer, RescheduleBySalesRepSerializer, RescheduleAllSerializer, EnableBySalesRepSerializer, IGFirstComplimentSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
# from django_tenants.utils import schema_context

from celery import current_app
import logging
# from django.db.models import QuerySet
import random
from datetime import time
import time as timer


from api.instagram.utils import lead_is_for_salesrep, tasks_by_sales_rep
from api.instagram.tasks import send_first_compliment
from .utils import *

class PaginationClass(PageNumberPagination):
    page_size = 20  # Set the number of items per page
    page_size_query_param = 'page_size'
    max_page_size = 100

class TasksViewSet(viewsets.ModelViewSet):
    queryset = PeriodicTask.objects.all()
    def get_serializer_class(self):
        if self.action == 'disable_all_tasks':
            return SingleTaskSerializer
        if self.action == 'enable_all_tasks':
            return SingleTaskSerializer
        if self.action == 'fetch':  
            return PeriodicTaskGetSerializer
        if self.action == 'fetch_by_sales_rep': 
            return TaskBySalesRepSerializer
        if self.action == 'reschedule_by_sales_rep': 
            return RescheduleBySalesRepSerializer
        if self.action == 'reschedule_all': 
            return RescheduleAllSerializer
        if self.action == 'disable_by_sales_rep': 
            return EnableBySalesRepSerializer
        if self.action == 'enable_by_sales_rep': 
            return EnableBySalesRepSerializer
        else:  
            return PeriodicTaskPostSerializer

    def list(self, request, *args, **kwargs):
        # Return an empty response for GET requests to the list endpoint
        return Response({})

    def create(self, request, *args, **kwargs):
        # Return a method not allowed response for POST requests to the root endpoint
        return Response({"message": "Method Not Allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    # instagram.tasks.send_first_compliment
    @action(detail=False, methods=['get'])
    def fetch(self, request):
        task_type = request.query_params.get('task', None)
        if task_type:
            queryset = self.queryset.filter(task=task_type)
        else:
            queryset = self.queryset.all()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def enable_all_tasks(self, request):
        task_name = request.data.get('task', None)  # Get the task name from request data
        if task_name:
            self.enableOrDisableAll(task_name, True)
            return Response({'message': f'Enabled all {task_name} tasks'})
        else:
            return Response({'error': 'Task name not provided'}, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['post'])
    def disable_all_tasks(self, request):
        task_name = request.data.get('task', None)  # Get the task name from request data
        if task_name:
            self.enableOrDisableAll(task_name, False)
            return Response({'message': 'Disabled all tasks'})
        else:
            return Response({'error': 'Task name not provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    # for now just use disable_all_tasks and select task_name
    # @action(detail=False, methods=['get'])
    # def enable_all_ig_first_compliment(self, request):
    #         self.enableOrDisableAll("instagram.tasks.send_first_compliment", True)
    #         return Response({'message': f'Enabled all IG first compliment tasks'})
        
    # @action(detail=False, methods=['get'])
    # def disable_all_ig_first_compliment(self, request):
    #         self.enableOrDisableAll("instagram.tasks.send_first_compliment", False)
    #         return Response({'message': 'Disabled all IG first compliment tasks'})

    def enableOrDisableAll(self, task_name, status):
        queryset = PeriodicTask.objects.filter(task=task_name)
        tasks = queryset.all()
        for task in tasks:
            status_to_save = status # for each task. status should remain unchanged
            if status_to_save: # if the task is to be enabled
                start_time = task.start_time
                status_to_save = rescheduled_task_is_in_future(start_time) # will only enable if task is in the future
            if task.enabled != status_to_save: # only change if task status is no the required status
                task.enabled = status_to_save 
                task.save()
                
    def enableOrDisableAllTaskList(self, tasks, status):
        for task in tasks:
            status_to_save = status  # for each task. status should remain unchanged
            if status_to_save: # if the task is to be enabled
                start_time = task.start_time
                status_to_save = rescheduled_task_is_in_future(start_time) # will only enable if task is in the future
            if task.enabled != status_to_save:
                task.enabled = status_to_save # enable oly future tasks
                task.save()
    @action(detail=False, methods=['post'])
    def fetch_by_sales_rep(self, request, task_name=None, sales_rep=None):
        serializer = TaskBySalesRepSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        task_name = validated_data.get('task', None)
        sales_rep = validated_data.get('sales_rep', None)
        status = validated_data.get('status', "any")
        order = validated_data.get('order', 1)
        number = validated_data.get('number', -1)
        return tasks_by_sales_rep(task_name, sales_rep, status, order, number)
    
    @action(detail=False, methods=['get'])
    def start_daily_rescheduler(self, request, *args, **kwargs):
        # get the time to start the outreaches
        # get the time here
        daily_start_time, start_minute, hours_per_day, tasks_per_day, _ = outreach_time()
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=start_minute,    
            hour=daily_start_time,      
            day_of_week='*',  
            day_of_month='*',  
            month_of_year='*',
            timezone='UTC'   # Important for UTC
        )
        # PeriodicTask.objects.filter(name="daily_reshedule_outreach").delete() 
        try:
            task = PeriodicTask.objects.get(name="daily_reshedule_outreach")
            task.crontab = schedule
            task.save()
        except PeriodicTask.DoesNotExist:
            # Task doesn't exist, create it!
            PeriodicTask.objects.create(
                enabled=True,
                task="api.outreaches.tasks.daily_reshedule_outreach",
                crontab=schedule,
                name="daily_reshedule_outreach"
            )
        return Response({'message': f'Enabled all tasks for'})
        
    @action(detail=False, methods=['post'])
    def reschedule_by_sales_rep(self, request, *args, **kwargs):
        serializer = RescheduleBySalesRepSerializer(data=request.data)

        # Check if the data is valid
        if serializer.is_valid():
            validated_data = serializer.validated_data
            task_name = validated_data['task_name']
            sales_rep = validated_data['sales_rep']
            start_hour = validated_data['start_hour']
            start_minute = validated_data['start_minute']
            # tasks_per_day = validated_data['tasks_per_day']
            num_tasks = validated_data['num_tasks']

            # sales_rep_names = []
            # sales_rep_names.append(sales_rep)

            
            start_hour = int(start_hour)  
            start_minute = int(start_minute)  

            start_time = datetime.now().replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)

            count = 1

            

            # for now we can make do with the hardcoded interval
            # hours_per_day = 12 # int(request.data.get('numperDay', 12))  # Get hours_per_day from request data
            # daily_start_time = 14
            daily_start_time, _, hours_per_day, tasks_per_day, _ = outreach_time()
            daily_end_time = daily_start_time + hours_per_day
            if daily_end_time >=24 :
                daily_end_time -= 24

            # for sales_rep_name in sales_rep_names:
            sales_rep_tasks = tasks_by_sales_rep("instagram.tasks.send_first_compliment", sales_rep)
            filtered_queryset = [] 
            if num_tasks != 0:
                for task in sales_rep_tasks.data['tasks']:
                    args_string = task['task']['args']
                    args_list = ast.literal_eval(args_string)
                    if args_list and len(args_list) > 0:
                        usernameInner = args_list[0]
                        if isinstance(usernameInner, list):
                            usernameInner = usernameInner[0]
                        thread_exists = ig_thread_exists(usernameInner)
                        if not thread_exists:  # Get salesrep_username from task 
                            filtered_queryset.append(task)
                            if num_tasks > 0 and count == num_tasks:
                                break 
                            count += 1
                        else:
                            print(f'Thread exist for {usernameInner}')
            queryset = filtered_queryset
            queryset = PeriodicTask.objects.filter(id__in=[task['task']['id'] for task in filtered_queryset])            

            tasks = scheduler_tasks(queryset, start_time, hours_per_day, tasks_per_day, daily_start_time, daily_end_time)
            for task in tasks:
                task.save()  # Save the task object to the database
                try:
                    PeriodicTask.objects.update_or_create(
                    # PeriodicTask.objects.create(
                        enabled=True,
                        name=task.name,
                        crontab=task.crontab,
                        task=task_name,  # Assuming you have a 'task_name' variable 
                        args=task.args      # Assuming your task has arguments
                    )
                except Exception as error:
                    logging.warning(error)  # Log any errors that might occur
            queryset = PeriodicTask.objects.filter(task=task_name).order_by('id')
            serializer = PeriodicTaskGetSerializer(queryset, many=True)
            return Response(serializer.data)
        else:
            # Return validation errors if data is invalid
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['post'])
    def reschedule_all(self, request, *args, **kwargs):
        serializer = RescheduleAllSerializer(data=request.data)

        # Check if the data is valid
        if serializer.is_valid():

            validated_data = serializer.validated_data
            task_name = validated_data['task_name']
            start_hour = validated_data['start_hour']
            start_minute = validated_data['start_minute']
            # tasks_per_day = validated_data['tasks_per_day']# remove
            num_tasks = validated_data['num_tasks']
            # sales_rep_names = []
            # sales_rep_names.append(sales_rep)

            
            start_hour = int(start_hour)  
            start_minute = int(start_minute)  

            start_time = datetime.now().replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)

            count = 1

            # for now we can make do with the hardcoded interval
            # get these from 
            # hours_per_day = 12 # int(request.data.get('numperDay', 12))  # Get hours_per_day from request data
            # daily_start_time = 14
            # import pdb;pdb.set_trace()
            daily_start_time, _, hours_per_day, tasks_per_day, _ = outreach_time()

            daily_end_time = daily_start_time + hours_per_day
            if daily_end_time >=24 :
                daily_end_time -= 24
            

            sales_rep_list = get_sales_reps()
            sales_rep_names = []
            sales_rep_names = [rep['ig_username'] for rep in sales_rep_list if 'ig_username' in rep] 

    
            for sales_rep_name in sales_rep_names:
                print(sales_rep_name)
                sales_rep_tasks = tasks_by_sales_rep("instagram.tasks.send_first_compliment", sales_rep_name)
                filtered_queryset = [] 
                if num_tasks != 0:
                    for task in sales_rep_tasks.data['tasks']:
                        args_string = task['task']['args']
                        args_list = ast.literal_eval(args_string)
                        if args_list and len(args_list) > 0:
                            usernameInner = args_list[0]
                            if isinstance(usernameInner, list):
                                usernameInner = usernameInner[0]
                            thread_exists = ig_thread_exists(usernameInner)
                            if not thread_exists:  # Get salesrep_username from task 
                                filtered_queryset.append(task)
                                if num_tasks > 0 and count == num_tasks:
                                    break 
                                count += 1
                            else:
                                print(f'Thread exist for {usernameInner}')
                queryset = filtered_queryset
                queryset = PeriodicTask.objects.filter(id__in=[task['task']['id'] for task in filtered_queryset])            

                tasks = scheduler_tasks(queryset, start_time, hours_per_day, tasks_per_day, daily_start_time, daily_end_time)
                for task in tasks:
                    task.save()  # Save the task object to the database
                    try:
                        PeriodicTask.objects.update_or_create(
                        # PeriodicTask.objects.create(
                            enabled=task.enabled, # enable only if the time is correct.
                            name=task.name,
                            crontab=task.crontab,
                            task=task_name,  # Assuming you have a 'task_name' variable 
                            args=task.args      # Assuming your task has arguments
                        )
                    except Exception as error:
                        logging.warning(error)  # Log any errors that might occur
                queryset = PeriodicTask.objects.filter(task=task_name).order_by('id')
            serializer = PeriodicTaskGetSerializer(queryset, many=True)
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['post'])
    def enable_by_sales_rep(self, request):
        serializer = EnableBySalesRepSerializer(data=request.data)

        if serializer.is_valid():
            salesrep = serializer.validated_data['salesrep']

            sales_rep_tasks = tasks_by_sales_rep("instagram.tasks.send_first_compliment", salesrep)
            filtered_queryset = [] 
            for task in sales_rep_tasks.data['tasks']:
                filtered_queryset.append(task)
            queryset = PeriodicTask.objects.filter(id__in=[task['task']['id'] for task in filtered_queryset])   
            self.enableOrDisableAllTaskList(queryset, True)
            return Response({'message': f'Enabled all tasks for {salesrep}'})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def disable_by_sales_rep(self, request):
        serializer = EnableBySalesRepSerializer(data=request.data)

        if serializer.is_valid():
            salesrep = serializer.validated_data['salesrep']

            sales_rep_tasks = tasks_by_sales_rep("instagram.tasks.send_first_compliment", salesrep)
            filtered_queryset = [] 
            for task in sales_rep_tasks.data['tasks']:
                filtered_queryset.append(task)
            queryset = PeriodicTask.objects.filter(id__in=[task['task']['id'] for task in filtered_queryset])   
            self.enableOrDisableAllTaskList(queryset, False)
            return Response({'message': f'Enabled all tasks for {salesrep}'})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TaskViewSet(viewsets.ModelViewSet):
    queryset = PeriodicTask.objects.all()
    serializer_mapping = {
        'disable': FirstComplimentSerializer,
        'enable': FirstComplimentSerializer,
        'reschedule': FirstComplimentSerializer,
        'send_first_compliment': IGFirstComplimentSerializer,
        # Add other actions and their corresponding serializer classes as needed
    }

    def get_serializer_class(self):
        """
        Return the serializer class based on the current action.
        """
        return self.serializer_mapping.get(self.action, PeriodicTaskPostSerializer)

    def list(self, request, *args, **kwargs):
        # Return an empty response for GET requests to the list endpoint
        return Response({})

    def create(self, request, *args, **kwargs):
        # Return a method not allowed response for POST requests to the root endpoint
        return Response({"message": "Method Not Allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    @action(detail=False, methods=['post'])
    def send_first_compliment(self, request):
        serializer = IGFirstComplimentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        user = validated_data.get('user', None)
        send_first_compliment(user)

        return Response({'message': f'Sent first compliment for: {user}'})
    
    @action(detail=False, methods=['post'])
    def enable(self, request):
        task_name = request.data.get('task', None)
        username = request.data.get('user', None) 

        if task_name and username:
            return process_task(task_name, username, True)  # Call the helper function
        else:
            return Response({'error': 'Task name and username are required'}, 
                            status=status.HTTP_400_BAD_REQUEST)
                            
    @action(detail=False, methods=['post'])
    def disable(self, request):
        task_name = request.data.get('task', None)
        username = request.data.get('user', None) 

        if task_name and username:
            return process_task(task_name, username, False)  # Call the helper function
        else:
            return Response({'error': 'Task name and username are required'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
    
        
    # just use enable_all and select IG task for now
    # @action(detail=False, methods=['post'])
    # def enable_ig_first_complimemt(self, request):
    #     username = request.data.get('user', None) 

    #     if  username:
    #         return process_task("instagram.tasks.send_first_compliment", username, True)  # Call the helper function
    #     else:
    #         return Response({'error': 'username is required'}, 
    #                         status=status.HTTP_400_BAD_REQUEST)
                            
    # @action(detail=False, methods=['post'])
    # def disable_ig_first_complimemt(self, request):
    #     username = request.data.get('user', None) 

    #     if username:
    #         return process_task("instagram.tasks.send_first_compliment", username, False)  # Call the helper function
    #     else:
    #         return Response({'error': 'username is required'}, 
    #                         status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['post'])
    def reschedule(self, request):
        
        task_name = request.data.get('task', None)  # Get the task name from request data
        username = request.data.get('user', None) 
        start_hour = request.data.get('startTime', '0')  # Get start_hour from request data # supplied time is in UTC
        start_minute = request.data.get('startMinute', '0')  # Get start_minute from request data
        tasks_per_day = int(request.data.get('numperDay', 24))  # Get tasks_per_day from request data
        if task_name  and username:
            return process_reschedule_single_task(task_name, username, start_hour, start_minute, tasks_per_day)
        else:
            return Response({'error': 'Task name and username are required'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
         
# class IGViewSet(viewsets.ModelViewSet):
#     queryset = PeriodicTask.objects.all()
#     def get_serializer_class(self):
#         if self.action == send_first_compliment:
#             return FirstComplimentSerializer
#         return FirstComplimentSerializer
    
#     @action(detail=False, methods=['post'])
#     def send_first_compliment(self, request):
#         serializer = FirstComplimentSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         validated_data = serializer.validated_data

#         task_name = validated_data.get('task', None)
#         user = validated_data.get('user', None)
#         send_first_compliment(user)

#         return Response({'message': f'Sent first compliment for: {user}'})
    
class PeriodicTaskViewSet(viewsets.ModelViewSet):
    queryset = PeriodicTask.objects.all()
    pagination_class = PaginationClass

    # @schema_context(os.getenv('SCHEMA_NAME'))
    # def list(self, request, *args, **kwargs):
    #     # Return an empty response for GET requests to the list endpoint
    #     return Response({})
    
    def get_serializer_class(self):
        if self.action == 'list':  # Use different serializer for list action
            return PeriodicTaskGetSerializer
        if self.action == 'disable_all_tasks':
            return SingleTaskSerializer
        if self.action == 'enable_all_tasks':
            return SingleTaskSerializer
        else:  # Use default serializer class for other actions
            return PeriodicTaskPostSerializer

 
    def create(self, request, *args, **kwargs):
        # Return a method not allowed response for POST requests to the root endpoint
        return Response({"message": "Method Not Allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    
    @action(detail=False, methods=['get'])
    def task_types(self, request, *args, **kwargs):
        task_types = self.queryset.values_list('task', flat=True).distinct()
        return Response(task_types)

