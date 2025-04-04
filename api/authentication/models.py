import uuid

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import Group, PermissionsMixin
from django.db import models
from django.utils import timezone

from api.helpers.models import BaseModel

from .managers import CustomUserManager

# Create your models here.


class User(BaseModel, AbstractBaseUser, PermissionsMixin):

    # These fields tie to the roles!
    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    uid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4, verbose_name="Public identifier")
    username = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    role = models.ForeignKey(Group, related_name="role", on_delete=models.CASCADE, blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(default=timezone.now)
    created_by = models.EmailField()
    modified_by = models.EmailField()
    status = models.TextField()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    @property
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class AccountRequest(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, null=False, related_name="account_requestor")
    requested_on = models.DateTimeField(auto_now_add=True)
    approved_rejected_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="account_approver")
    approved_rejected_on = models.DateTimeField(null=True)
    rejection_reason = models.TextField(null=True)
