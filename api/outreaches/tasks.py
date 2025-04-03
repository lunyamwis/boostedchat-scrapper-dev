from celery import shared_task
from django.conf import settings
import requests
from .utils import *

@shared_task()
def daily_reshedule_outreach():
    daily_start_time, start_minute, hours_per_day, tasks_per_day, _ = outreach_time()
    data = {
        'task_name': "instagram.tasks.send_first_compliment",
        'start_hour': daily_start_time,
        'start_minute': start_minute
    }

    json_data = json.dumps(data)
    response = requests.post(settings.API_BASE_URL + "/outreaches/tasks/reschedule_all/", data=json_data, headers={"Content-Type": "application/json"})

    # Check the response status code
    if response.status_code == 200:
        print("POST request successful.")
    else:
        print(f"POST request failed with status code: {response.status_code}")
