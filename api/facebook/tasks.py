from apify_client import ApifyClient
from celery import shared_task
import os

# You can find your API token at https://console.apify.com/settings/integrations.
TOKEN = os.getenv('APIFY_TOKEN')

@shared_task()
def call_actor(name_of_actor) -> None:
    apify_client = ApifyClient(TOKEN)

    # Start an Actor and wait for it to finish.
    actor_client = apify_client.actor(name_of_actor)
    call_result = actor_client.call()

    if call_result is None:
        print('Actor run failed.')
        return

    # Fetch results from the Actor run's default dataset.
    dataset_client = apify_client.dataset(call_result['defaultDatasetId'])
    list_items_result = dataset_client.list_items()
    print(f'Dataset: {list_items_result}')