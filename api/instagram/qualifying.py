from django.db.models import Q
from django.utils import timezone
from api.instagram.models import Account
from django_tenants.utils import schema_context
import os
import math

with schema_context(os.environ.get("SCHEMA_NAME")):
    # Your code that requires the tenant schema context goes here
    
    barber_keywords = [
    "hair",
    "appointment",
    "appointments",
    "book",
    "call",
    "book.thecut.co",
    "licensed",
    "cutz",
    "kutz",
    "cuts",
    "cut",
    "hairstylist",
    "salon",
    "salons",
    "educator",
    "specialist",
    "beauty",
    "barber",
    "walk",
    "text",
    "stylist",
    "colour",
    "colouring",
    "loreal",
    "olaplex",
    "hairspray",
    "mousse",
    "pomade",
    "hair oil",
    "hair serum",
    "scissors",
    "fades",
    "fade",
    "faded",
    "comb",
    "brush",
    "blow dryer",
    "flat iron",
    "curling iron",
    "hair rollers",
    "hair clips",
    "hair ties",
    "headbands",
    "hair accessories",
    "updos",
    "braids",
    "twists",
    "buns",
    "ponytails",
    "curls",
    "waves",
    "volume",
    "texture",
    "shine",
    "frizz control",
    "breakage",
    "dryness",
    "oiliness",
    "thinning",
    "hair loss",
    "dandruff",
    "scalp problems",
    ]

    # Create a Q object for filtering
    query = Q()
    for keyword in barber_keywords:
        query |= Q(igname__icontains=keyword)

    yesterday = timezone.now() - timezone.timedelta(days=7) # filter on a weekly basis

    # Filter accounts using the query
    filtered_accounts = Account.objects.filter(query).filter(created_at__gte=yesterday).exclude(status__name="sent_compliment")

    for account in filtered_accounts:
        account.qualified = True
        account.engagement_version = "1"
        account.created_at = timezone.now()
        account.save()
    print(filtered_accounts.count())


    # Split to run for x days automatically
    number_outreach_per_day = 24
    total_outreach_days = round(filtered_accounts.count()/number_outreach_per_day)
    day_schedule_accounts = [{"day": 0}]
    day_to_schedule = 0
    accounts_index = 0




    while accounts_index < len(filtered_accounts):
        
        print(accounts_index)
        if day_schedule_accounts[-1]['day'] == total_outreach_days:
            break
        
        day_to_schedule += 1
        
        # Distribute accounts for this day
        for _ in range(number_outreach_per_day):
            if accounts_index >= len(filtered_accounts):
                break
            day_schedule_accounts.append({
                "day": day_to_schedule,
                "account": filtered_accounts[accounts_index]
            })
            
            accounts_index += 1

    # Remove the initial placeholder
    if day_schedule_accounts[0]['day'] == 0 and len(day_schedule_accounts) > 1:
        day_schedule_accounts.pop(0)


    print(len(day_schedule_accounts))
    for account in day_schedule_accounts:
        account['account'].created_at = timezone.now() + timezone.timedelta(days = account['day']-1,)
        account['account'].outreach_time = timezone.now() + timezone.timedelta(days = account['day']-1)
        account['account'].save()
        # pass


    day_schedule_accounts

