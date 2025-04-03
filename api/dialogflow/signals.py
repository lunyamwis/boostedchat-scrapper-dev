from django.core.signals import request_finished
from django.dispatch import receiver

from .models import RequestTracker


@receiver(request_finished)
def update_request_count(sender, **kwargs):
    tracker, created = RequestTracker.objects.get_or_create(pk=1)
    tracker.request_count += 1
    tracker.save()
