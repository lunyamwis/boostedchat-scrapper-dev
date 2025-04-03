from datetime import datetime, timedelta
from django.utils import timezone
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import random
from api.instagram.models import Thread, Account
from rest_framework.response import Response
import logging
from datetime import time
import time as timer
from .serializers import PeriodicTaskPostSerializer, TaskBySalesRepSerializer, FirstComplimentSerializer, PeriodicTaskGetSerializer
from rest_framework import status
import json
from api.sales_rep.models import SalesRep
from api.authentication.models import User
import requests
import pytz
from django.conf import settings


def time_parts(time):
    return time.year, time.month, time.day, time.hour, time.minute

def add_minutes_to_time(input_time, minutes): # interval is in minutes
    if isinstance(input_time, datetime):
        try:
            # Create a timedelta object with the specified number of minutes
            time_delta = timedelta(minutes=minutes)
            # Add the timedelta to the input time
            new_time = input_time + time_delta
            return new_time  # Return the new time as a datetime object
        except ValueError:
            print("wrong minutes")
            return None  # Handle invalid time format
    else:
        print("is not date time")
        return None  # Handle non-datetime input

def get_task_interval_minutes(hours_per_day, tasks_per_day):
    if tasks_per_day < 0 or hours_per_day < 0:
        raise ValueError("Hours per day and tasks per day must be non-negative.")
    if tasks_per_day == 0 or hours_per_day == 0:
        return 0
    return (hours_per_day * 60) // tasks_per_day  # use integer division

def randomize_interval(interval_minutes, seed_minutes, direction):
    if interval_minutes < 0 or seed_minutes < 0:
        raise ValueError("interval_minutes and seed_minutes must be non-negative")
    interval_head = int(0.25 * interval_minutes)  # Convert interval_head to an integer

    if direction == 0:
        # Random integer between -interval_head and +interval_head
        random_value = random.randint(-interval_head, interval_head)
    elif direction == -1:
        # Random integer between -interval_head and 0
        random_value = random.randint(-interval_head, 0)
    elif direction == 1:
        # Random integer between 0 and +interval_head
        random_value = random.randint(0, interval_head)
    else:
        raise ValueError("Invalid direction. Direction should be -1, 0, or 1.")

    return random_value + seed_minutes  # Add the random value to the seed_minutes

def get_first_time(start_time, interval_minutes):
    interval_minutes = randomize_interval(interval_minutes, 0, 1)
    print(f'=>{start_time}')
    print(f'=========>{interval_minutes}')
    return add_minutes_to_time(start_time, interval_minutes)

def get_next_time(current_time, interval_minutes):
    interval_minutes = randomize_interval(interval_minutes, interval_minutes, 0)
    return add_minutes_to_time(current_time, interval_minutes)

def not_in_interval(current_task_time = -1, daily_start_time = -1, daily_end_time = -1): # Assumes tasks will always start at the top of the hour
    if daily_start_time == -1 or daily_end_time == -1:
        db_daily_start_time, _, _, _, end_hour = outreach_time()
        if daily_start_time == -1:
            daily_start_time = db_daily_start_time
        if daily_end_time == -1:
            daily_end_time = end_hour

    if current_task_time == -1:
        current_task_time = timezone.now() # datetime.now(timezone.utc) does not work in the ms. works here. Why?
    start_hour = daily_start_time
    stop_hour = daily_end_time
    current_hour = current_task_time.hour  # Get the hour from current_task_time
    
    if stop_hour == start_hour:
        return False  # always in work interval
    if stop_hour < start_hour:
        if current_hour >= start_hour or current_hour < stop_hour:
            return False  # in work interval
        return True 
    if current_hour >= start_hour and current_hour < stop_hour:
        return False  # in work interval
    return True

# enable task only if it is in the future
def rescheduled_task_is_in_future(current_task_time):
    try:
        current_time = timezone.now()
        return current_task_time >= current_time
    except TypeError:  # Handle if current_task_time is timezone-naive
        current_time = datetime.now()
        return current_task_time >= current_time

# run = 0
def put_within_working_hour(current_task_time, start_hour, stop_hour ):
    # global run 
    stop_hour_init = stop_hour
    if not_in_interval(current_task_time, start_hour, stop_hour):
        working_interval = stop_hour - start_hour
        if stop_hour < start_hour:
            working_interval += 24
        not_working_interval = 24 - working_interval
        current_task_time = add_minutes_to_time(current_task_time, not_working_interval * 60)
        if not_in_interval(current_task_time, start_hour, stop_hour):
            # print(f'300==> {current_task_time}...{start_hour}, {stop_hour}')
            # run += 1
            # if run == 10:
            #     raise Exception(f"func error ")
            current_task_time = put_within_working_hour(current_task_time, start_hour, stop_hour_init )
        else:
            run = 0
    return current_task_time

def chron_parts(chron):
    current_year = datetime.now().year
    return current_year, chron.month_of_year, chron.day_of_month, chron.hour, chron.minute
    
def scheduler_tasks(tasks, start_time, hours_per_day, tasks_per_day, daily_start_time, daily_end_time): 
    interval_minutes = get_task_interval_minutes(hours_per_day, tasks_per_day)
    print(start_time, interval_minutes)
    current_task_time = get_first_time(start_time, interval_minutes)
    print(current_task_time, interval_minutes)
    current_task_time = put_within_working_hour(current_task_time, daily_start_time, daily_end_time )
    print(current_task_time)

    for task in tasks:
        year, month, day, hour, minute = time_parts(current_task_time)
        scheduler_datetime = timezone.datetime(year=year, month=month, day=day, hour=hour, minute=minute)
        crontab_schedule = CrontabSchedule.objects.create(
                    minute=scheduler_datetime.minute,
                    hour=scheduler_datetime.hour,
                    day_of_month=scheduler_datetime.day,
                    month_of_year=scheduler_datetime.month,
                    timezone='UTC'  # Set the timezone explicitly
                )
        task.enabled = rescheduled_task_is_in_future(current_task_time)
        task.start_time = scheduler_datetime  
        task.crontab = crontab_schedule


        # if not task.enabled:
        #     print(task)
        # task.enabled = False ## check...
        # task.save()
        # try:
        #     PeriodicTask.objects.update_or_create(
        #         name=task.name,
        #         crontab=task.crontab,
        #         task=task_name,
        #         args=task.args
        #     )
        
        # except Exception as error:
        #     logging.warning(error)

        current_task_time = get_next_time(current_task_time, interval_minutes)
        current_task_time = put_within_working_hour(current_task_time, daily_start_time, daily_end_time )

    return tasks # save where this is called from

def process_task(task_name, username, enable=True):
        queryset = PeriodicTask.objects.filter(task=task_name, name=username)

        if queryset.exists():
            for task in queryset:
                if task.enabled == enable:  # Check if already in the desired state
                    return Response({'error': f'Task is already {"enabled" if enable else "disabled"}'}, 
                                    status=status.HTTP_422_UNPROCESSABLE_ENTITY)

                task.enabled = enable
                task.save()
                return Response({'message': f'Task {"enabled" if enable else "disabled"}'})
        else:
            return Response({'error': f'Task: {task_name} not found for {username}'}, 
                            status=status.HTTP_404_NOT_FOUND)

def process_reschedule_single_task(task_name, username, start_hour, start_minute, tasks_per_day=24):
    queryset = PeriodicTask.objects.filter(task=task_name, name=username).order_by('-id')
    filtered_queryset = [] 
    if queryset.exists():
        for task in queryset:
            args_json = task.args
            args_list = json.loads(args_json)
            if args_list and len(args_list) > 0:
                usernameInner = args_list[0]
                if isinstance(usernameInner, list):
                    usernameInner = usernameInner[0]
                thread_exists = ig_thread_exists(usernameInner)
                if not thread_exists:  # Get salesrep_username from task 
                    filtered_queryset.append(task)
                else:
                    print(f'Thread exist for {usernameInner}')
    queryset = filtered_queryset
    queryset = PeriodicTask.objects.filter(id__in=[task.id for task in filtered_queryset])

    # serializer = self.get_serializer(queryset, many=True)
    start_hour = int(start_hour)  # Convert start_hour to integer if it's not already
    start_minute = int(start_minute)  # Convert start_minute to integer if it's not already

    # start_time = time(hour=start_hour, minute=start_minute)
    start_time = datetime.now().replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)

    # for now we can make do with the hardcoded interval
    hours_per_day = 12 # int(request.data.get('numperDay', 12))  # Get hours_per_day from request data
    daily_start_time = 14
    daily_end_time = daily_start_time + hours_per_day
    if daily_end_time >=24 :
        daily_end_time -= 24

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
    queryset = PeriodicTask.objects.filter(task=task_name, name=username).order_by('id')
    serializer = PeriodicTaskGetSerializer(queryset, many=True)
    return Response(serializer.data)


def get_sales_reps():
    reps = SalesRep.objects.filter(available=True)
    user_info = []
    for rep in reps:
        if User.objects.filter(id=rep.user.id).exists():
            info = {"user": User.objects.filter(id=rep.user.id).values(), "instagram": rep.instagram.values(),
                    "ig_username": rep.ig_username, "ig_password": rep.ig_password, "country": rep.country, "city": rep.city}
            user_info.append(info)

    return user_info

def ig_thread_exists(username):
    try:
        first_account = Account.objects.filter(igname="".join(username)).first()
        last_account = Account.objects.filter(igname="".join(username)).last()
        if first_account.salesrep_set.filter().exists():
            account = first_account
        elif last_account.salesrep_set.filter().exists():
            account = last_account
    except Exception as error:
        print(error)
        return True # assume true
    salesrep = account.salesrep_set.first()
    ig_username = salesrep.ig_username
    print(f'Checking....{username}=>{ig_username}')
    if  Thread.objects.filter(account__igname=username, account__salesrep__ig_username=ig_username): # try this one tomorrow
    # if  Thread.objects.filter(account__igname=username):
        print(f"exist for /|\\")
        return True
    else:
        return False

def round_to_nearest_hour(dt):
    minutes_past_hour = dt.minute
    offset_to_round = timedelta(minutes=minutes_past_hour)

    if minutes_past_hour >= 30:
        return dt - offset_to_round + timedelta(hours=1) 
    else:
        return dt - offset_to_round

def outreach_time():
    try:
        url = settings.SCRAPPER_BASE_URL + '/instagram/schedulers/'
        print(url)
        # Send a GET request to the URL and fetch the JSON response
        response = requests.get(url)
        data = response.json()

        # Check if data is not empty and contains at least one object
        if data and isinstance(data, list) and len(data) >= 1:
            # Get the first object from the list
            first_object = data[0]
            # Extract timezone, outreach capacity, outreach start time, and outreach end time
            timezone = first_object.get('timezone', 'N/A')

            outreach_capacity = first_object.get('outreach_capacity', 'N/A')
            outreach_starttime_str = first_object.get('outreach_starttime', 'N/A')
            outreach_endtime_str = first_object.get('outreach_endtime', 'N/A')

            # Convert times to UTC if timezone is specified
            if timezone != 'N/A':
                original_timezone = pytz.timezone(timezone)
                outreach_starttime = original_timezone.localize(datetime.strptime(outreach_starttime_str, '%H:%M:%S'))
                outreach_endtime = original_timezone.localize(datetime.strptime(outreach_endtime_str, '%H:%M:%S'))
                outreach_starttime_utc = outreach_starttime.astimezone(pytz.utc)
                outreach_endtime_utc = outreach_endtime.astimezone(pytz.utc)
            else:
                outreach_starttime_utc = 'N/A'
                outreach_endtime_utc = 'N/A'

            outreach_starttime_utc = round_to_nearest_hour(outreach_starttime_utc)
            outreach_endtime_utc = round_to_nearest_hour(outreach_endtime_utc)

            if outreach_endtime_utc < outreach_starttime_utc:
                outreach_endtime_utc += timedelta(days=1)  

            duration = outreach_endtime_utc - outreach_starttime_utc
            # duration = duration.replace(minute=0, second=0, microsecond=0) 
            hours_per_day = int(duration.total_seconds() // 3600)  # Calculate hours using total seconds

            start_hour = outreach_starttime_utc.hour
            start_minute = outreach_starttime_utc.minute

            # Convert start_hour and start_minute to integers
            start_hour = int(start_hour)
            start_minute = int(start_minute)
            end_hour = start_hour + hours_per_day
            if end_hour > 23:
                end_hour -= 24
            # return start hours, start minutes, stop.. duration, capacity, hours_per_day
            return start_hour, start_minute, hours_per_day, outreach_capacity, end_hour

        else:
            print("No data or empty response received.")
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None