from django.db.models import Q
   ...: from api.instagram.models import Account,UnwantedAccount
   ...: from django_tenants.utils import schema_context
   ...: from django.utils import timezone
   ...: import os
   ...: with schema_context(os.getenv('SCHEMA_NAME')):
   ...:     yesterday = timezone.now().date() - timezone.timedelta(days=1)
   ...:     tomorrow = timezone.now().date() + timezone.timedelta(days=1)
   ...:     yesterday_start = timezone.make_aware(timezone.datetime.combine(yesterday, timezone.datetime.min.time()))
   ...:     unwanted_usernames = UnwantedAccount.objects.values_list('username', flat=True)
   ...: 
   ...:     # Filter accounts that are qualified and created from yesterday onwards, and exclude accounts that are not wanted
   ...:     accounts = Account.objects.filter(
   ...:         Q(qualified=True) & Q(created_at__gte=yesterday_start) & Q(created_at__lte=tomorrow)
   ...:     ).exclude(
   ...:         status__name="sent_compliment"
   ...:     ).exclude(
   ...:         igname__in=unwanted_usernames
   ...:     )
   ...:     print(accounts.count())
   ...:     for i,account in enumerate(accounts):
   ...:         if i == 10:
   ...:             break
   ...:         account.dormant_profile_created=False
   ...:         account.save()
