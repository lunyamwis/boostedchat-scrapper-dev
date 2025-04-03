# Create your models here.
# models.py

from django.db import models


class RequestTracker(models.Model):
    request_count = models.PositiveIntegerField(default=0)
