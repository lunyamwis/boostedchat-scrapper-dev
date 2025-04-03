import time
from datetime import datetime, timedelta
from api.instagram.tasks import send_first_compliment

def run_scheduler(target_time,username,message):
    """
    A custom scheduler to execute a task at the specified target time.
    
    :param target_time: The datetime object specifying when to run the task.
    """
    print(f"Scheduler started. Current time: {datetime.now()}, Target time: {target_time}")
    
    while True:
        now = datetime.now()
        if now >= target_time:
            send_first_compliment(username,message)
            break  # Exit the loop after running the task
        time.sleep(1)  # Sleep for 1 second to avoid busy-waiting

