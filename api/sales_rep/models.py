from django.db import models
from django.utils import timezone
from api.authentication.models import User
from api.helpers.models import BaseModel
from api.instagram.models import Account


# Create your models here.
class SalesRep(BaseModel):
    STATUS_CHOICES = (
        (0,'AVAILABLE'),
        (1,'ACTIVE'),
        (2,'CHALLLENGE REQUIRED')
    )
    app_version = models.CharField(max_length=25,null=True, blank=True)
    android_version = models.IntegerField(null=True, blank=True)
    android_release = models.CharField(max_length=20,null=True, blank=True)
    dpi=models.CharField(max_length=27,null=True, blank=True)
    resolution=models.CharField(max_length=20,null=True, blank=True)
    manufacturer = models.CharField(max_length=30,null=True, blank=True)
    device = models.CharField(max_length=22,null=True, blank=True)
    model = models.CharField(max_length=22,null=True, blank=True)
    cpu = models.CharField(max_length=20,null=True, blank=True)
    version_code = models.CharField(max_length=22,null=True, blank=True)
    status = models.IntegerField(choices=STATUS_CHOICES,default=0,null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ig_username = models.CharField(max_length=255, null=True, blank=True)
    ig_password = models.CharField(max_length=255, null=True, blank=True)
    instagram = models.ManyToManyField(Account, blank=True)
    available = models.BooleanField(default=True)
    country = models.TextField(default="US")
    city = models.TextField(default="Pasadena")
    zip = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self) -> str:
        return self.ig_username


class Influencer(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ig_username = models.CharField(max_length=255, null=True, blank=True)
    ig_password = models.CharField(max_length=255, null=True, blank=True)
    instagram = models.ManyToManyField(Account, blank=True)
    available = models.BooleanField(default=True)
    country = models.TextField(default="US")
    city = models.TextField(default="Pasadena")

    def __str__(self) -> str:
        return self.user.email

class LeadAssignmentHistory(models.Model):
    influencer = models.ForeignKey(Influencer, on_delete=models.CASCADE,null=True,blank=True)
    sales_rep = models.ForeignKey(SalesRep, on_delete=models.CASCADE,null=True,blank=True)
    lead = models.ForeignKey(Account, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return self.sales_rep.ig_username +"=====>"+self.lead.igname