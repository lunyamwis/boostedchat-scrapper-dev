from django.db import models
from api.helpers.models import BaseModel
from django.contrib.postgres.fields import ArrayField
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models.signals import post_save,pre_save
from django.dispatch import receiver
from django.utils import timezone
from api.scout.models import Scout
import pytz
from django.core.exceptions import ValidationError
from django.db.models import OuterRef, Subquery, Count, Q, F, Value
from django.utils import timezone
from django.db.models.functions import Coalesce
from datetime import datetime
from django_tenants.utils import schema_context
import os

# Create your models here.
class Score(BaseModel):
    CRITERIA = (
        (0, 'none'),
        (1, 'type of keywords and number'),
        (2, 'number of times lead found during scrapping'),
        (3, 'negative points when disqualifying them'),
        (4, 'progress through sales funnel')
    )
    MEASURES = (
        (0, 'percentage'),
        (1, 'probability'),
        (2, 'linear scale')
    )
    name = models.CharField(max_length=255)
    criterion = models.IntegerField(choices=CRITERIA, default=0)
    measure = models.IntegerField(choices=MEASURES, default=0)
    linear_scale_capacity = models.IntegerField(blank=True, null=True)
    

class QualificationAlgorithm(BaseModel):
    name = models.CharField(max_length=255)
    positive_keywords = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    number_positive_keywords = models.IntegerField()
    negative_keywords = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    number_negative_keywords = models.IntegerField()
    score = models.ForeignKey(Score, on_delete=models.CASCADE, null=True, blank=True)


class Scheduler(BaseModel):
    TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.all_timezones]
    name = models.CharField(max_length=255)
    timezone = models.CharField(max_length=63, choices=TIMEZONE_CHOICES, default='UTC')
    outreach_capacity = models.IntegerField()
    outreach_starttime = models.TimeField()
    outreach_endtime = models.TimeField()
    scrapper_starttime = models.DateTimeField()
    scrapper_endtime = models.DateTimeField(null=True,blank=True)



class LeadSource(BaseModel):
    CRITERIA = (
        (0, 'get similar accounts'),
        (1, 'get followers'),
        (2, 'get users'),
        (3, 'get posts with hashtag'),
        (4, 'interacted with photos'),
        (5, 'to be enriched from instagram'),
        (6, 'google maps'),
        (7, 'urls'),
        (8, 'apis')
    )
    name = models.CharField(max_length=255)
    criterion = models.IntegerField(choices=CRITERIA, default=0)
    account_usernames = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    estimated_usernames = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    photo_links = ArrayField(models.URLField(), blank=True, null=True)
    external_urls = ArrayField(models.URLField(), blank=True, null=True)
    hashtags = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    google_maps_search_keywords = models.TextField(blank=True, null=True)
    enrich_with_url_in_bio = models.BooleanField(default=True)
    is_infinite_loop = models.BooleanField(default=True)



class InstagramUser(BaseModel):
    SOURCE_CHOICES = (
        (1, 'followers'),
        (2, 'searching_users'),
        (3, 'similar_accounts'),
    )
    username = models.CharField(max_length=255,null=True,blank=True)
    info = models.JSONField(null=True,blank=True)
    linked_to = models.CharField(max_length=50,null=True,blank=True)
    source = models.IntegerField(choices=SOURCE_CHOICES,default=1)
    round = models.IntegerField(null=True,blank=True)
    scout = models.ForeignKey(Scout,on_delete=models.CASCADE,null=True,blank=True)
    account_id = models.CharField(max_length=255,null=True,blank=True)
    account_id_pointer = models.BooleanField(default=False)
    outsourced_id = models.CharField(max_length=255,null=True,blank=True)
    outsourced_id_pointer = models.BooleanField(default=False)
    qualified_keywords = models.TextField(null=True, blank=True)
    qualified = models.BooleanField(default=False)
    scraped = models.BooleanField(default=False)
    relevant_information = models.JSONField(null=True,blank=True)
    influencer_source_key = models.CharField(max_length=255,null=True,blank=True)
    thread_id = models.CharField(max_length=255,null=True,blank=True)
    item_id = models.CharField(max_length=255,null=True,blank=True)
    user_id = models.CharField(max_length=255,null=True,blank=True)
    item_type = models.CharField(max_length=255,null=True,blank=True)
    timestamp = models.CharField(max_length=255,null=True,blank=True)
    cursor = models.TextField(null=True,blank=True)
    is_manually_triggered = models.BooleanField(default=False)
    

    def __str__(self) -> str:

        return self.username if self.username else 'cursor'





class Media(BaseModel):
    MEDIA_TYPES = (
        ('image', 'Image'),
        ('video', 'Video'),
        ('carousel', 'Carousel'),
        ('story', 'Story'),
        ('igtv', 'IGTV'),
    )
    media_type = models.CharField(max_length=255, choices=MEDIA_TYPES,default='image')
    media_url = models.URLField(null=True,blank=True)
    caption = models.TextField(null=True,blank=True)
    user = models.ForeignKey(InstagramUser, on_delete=models.CASCADE,null=True,blank=True)
    timestamp = models.DateTimeField(null=True,blank=True)
    item_id = models.CharField(max_length=255,null=True,blank=True)
    item_type = models.CharField(max_length=255,null=True,blank=True)
    download_url = models.URLField(max_length=2048,null=True,blank=True)
    
    

    def __str__(self) -> str:
        return self.media_url
    


class OutSourcedInfo(models.Model):
    source = models.CharField(null=True, blank=True, max_length=255)
    results = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)


class StatusCheck(BaseModel):
    STAGES = ((1, "Oven"), (2, "Needs Assessment"), (3, "Overcoming Objections"), (4, "Activation"))
    stage = models.IntegerField(choices=STAGES, default=1)
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.stage} - {self.name}"

    def get_id(self):
        return self.id


class UnwantedAccount(BaseModel):
    username = models.CharField(max_length=255, null=True, blank=True, unique=False)

    def __str__(self) -> str:
        return self.username if self.username else self.id


class AccountManager(models.Manager):
    @schema_context(os.getenv('SCHEMA_NAME'))
    def to_follow_up(self):
        max_days = 360 # don’t go back infinitely, e.g., up to ~1 year 
        days_step = 30
        for i in range(1, (max_days // days_step) + 1):
            days_ago = i * days_step
            
            print(f"Trying threshold: last {days_ago} days")

            date_threshold = timezone.now() - timezone.timedelta(days=days_ago)
            # date_threshold = timezone.now() - timezone.timedelta(days=30)

            # Latest account per igname
            latest_accounts_subquery = (
                self.model.objects
                .filter(igname=OuterRef('igname'))
                .order_by('-created_at')
            )

            # Last two messages in the thread
            last_message_subquery = (
                Message.objects
                .filter(thread=OuterRef('thread'))
                .order_by('-sent_on')
            )
            second_last_message_subquery = (
                Message.objects
                .filter(thread=OuterRef('thread'))
                .order_by('-sent_on')[1:2]
            )

            qs = (
                self.get_queryset()
                .filter(
                    qualified=True,
                    question_asked=False,
                    status__name='sent_compliment',
                    created_at__gte=date_threshold
                )
                .annotate(
                    client_message_count=Count(
                        'thread__message',
                        filter=Q(thread__message__sent_by='Client')
                    ),
                    last_message_sent_by=Subquery(
                        last_message_subquery.values('sent_by')[:1]
                    ),
                    second_last_message_sent_by=Subquery(
                        second_last_message_subquery.values('sent_by')
                    ),
                    last_message_sent_on=Subquery(
                        last_message_subquery.values('sent_on')[:1]
                    )
                )
                .filter(
                    last_message_sent_by='Robot',
                    #client_message_count=0,# never replied
                    client_message_count__gt=1,  # have replied
                    created_at=Subquery(latest_accounts_subquery.values('created_at')[:1])
                )
                .exclude(
                    second_last_message_sent_by='Robot'
                )
                .order_by('-last_message_sent_on')  # freshest activity first
            )
            print(list(qs.values_list('igname', flat=True)))
            account =  qs.first()  # return the single freshest account, or use .all() to get list
            if account:
                thread = account.thread_set.last() if account else None
                if thread is None:
                    queryset = (
                        Thread.objects
                        .select_related('account')
                        .filter(
                            account__salesrep__isnull=False,
                            account__igname=account.igname   # or use icontains=search_query if partial
                        )
                        .annotate(
                            last_message_at_ordering=Coalesce('last_message_at', Value(datetime.min))
                        )
                        .order_by(F('last_message_at_ordering').desc())
                    )
                    thread = queryset.last() if queryset.exists() else None
                
                if thread:
                    return account
            
            if days_ago >= 360:  # limit to 1 year
                break
        return None  # if no account found in the iterations
        

class Account(BaseModel):
    igname = models.CharField(max_length=255, null=True, unique=False, blank=True)
    assigned_to = models.TextField(default="Robot")
    referral = models.TextField(default="",null=True,blank=True)
    full_name = models.CharField(max_length=1024, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=255, null=True, blank=True)
    profile_url = models.URLField(null=True, blank=True)
    status = models.ForeignKey(StatusCheck, on_delete=models.CASCADE, null=True, blank=True)
    script_score = models.IntegerField(null=True, blank=True)
    script_version = models.CharField(max_length=255,null=True,blank=True)
    status_param = models.CharField(max_length=255, null=True, unique=False, blank=True)
    confirmed_problems = models.TextField(null=True, blank=True, default="test")
    solution_presented = models.BooleanField(default=False)
    question_asked = models.BooleanField(default=False)
    rejected_problems = models.TextField(null=True, blank=True, default="test")
    linked_to = models.CharField(max_length=255, null=True, blank=True, default="no_one")
    # history = AuditlogHistoryField(pk_indexable=False)
    dormant_profile_created = models.BooleanField(default=False, null=True, blank=True) # used to check if LLM creates for them a dormant profile
    qualified = models.BooleanField(default=False)
    scraped = models.BooleanField(default=False)
    relevant_information = models.JSONField(null=True,blank=True)
    is_manually_triggered = models.BooleanField(default=False)
    index = models.IntegerField(default=1)
    notes = models.TextField(null=True, blank=True)  # New notes field
    outreach_time = models.DateTimeField(null=True, blank=True)
    outreach_success = models.BooleanField(default=False)
    responded_date = models.DateField(null=True, blank=True)
    call_scheduled_date = models.DateField(null=True, blank=True)
    closing_date = models.DateField(null=True, blank=True)
    won_date = models.DateField(null=True, blank=True)
    success_story_date = models.DateField(null=True, blank=True)
    lost_date = models.DateField(null=True, blank=True)
    engagement_version = models.CharField(max_length=255, null=True, blank=True, default="1")
    sales_qualified_date = models.DateField(null=True, blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_count = models.IntegerField(default=0)
    objects = AccountManager()

    def __str__(self) -> str:
        return self.igname if self.igname else self.id
    

class OutSourced(BaseModel):
    source = models.CharField(null=True, blank=True, max_length=255)
    results = models.JSONField()
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.account.igname}==>{self.id}" if self.account else self.id
    
# auditlog.register(Account)


class HashTag(BaseModel):
    hashtag_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255, null=True, blank=True)


class Story(BaseModel):
    story_id = models.CharField(max_length=50, null=True, blank=True)
    link = models.URLField()


class Photo(BaseModel):
    photo_id = models.CharField(max_length=50)
    link = models.URLField()
    name = models.CharField(max_length=255)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)


class Thread(BaseModel):
    thread_id = models.CharField(max_length=255)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    unread_message_count = models.IntegerField(default=0)
    last_message_content = models.TextField(null=True, blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True)


class Message(BaseModel):
    content = models.TextField(null=True, blank=True, default="test")
    sent_by = models.CharField(max_length=255, null=True, blank=True)
    sent_on = models.DateTimeField()
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, null=True, blank=True)
    # New fields
    content_type = models.CharField(max_length=255, null=True, blank=True)
    content_link = models.CharField(max_length=255, null=True, blank=True)
    content_data = models.JSONField(null=True, blank=True)  # Use JSONField for storing JSON data 
    message_id = models.CharField(max_length=50, null=True, blank=True)


class Video(BaseModel):
    video_id = models.CharField(max_length=50)
    link = models.URLField()
    name = models.CharField(max_length=255)


class Reel(BaseModel):
    reel_id = models.CharField(max_length=50)
    link = models.URLField()
    name = models.CharField(max_length=255)
    
class Comment(BaseModel):
    comment_id = models.CharField(max_length=50)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    media_id =  models.CharField(max_length=255, null=True, blank=True)
    target_comment_id =  models.CharField(max_length=255, null=True, blank=True)
    collapseKey =  models.CharField(max_length=50, null=True, blank=True)
    optionalAvatarUrl = models.URLField(null=True, blank=True,max_length=2048)
    pushId =  models.CharField(max_length=255, null=True, blank=True)
    pushCategory = models.CharField(max_length=255, null=True, blank=True)
    intendedRecipientUserId = models.CharField(max_length=50, null=True, blank=True)
    sourceUserId=  models.CharField(max_length=50, null=True, blank=True)

    def __str__(self) -> str:
        return self.message if self.message else self.id 
    
class Like(BaseModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    media_id =  models.CharField(max_length=255, null=True, blank=True)
    collapseKey = models.CharField(max_length=50, null=True, blank=True)
    optionalAvatarUrl = models.URLField( null=True, blank=True,max_length=2048)
    pushId =  models.CharField(max_length=50, null=True, blank=True)
    pushCategory = models.CharField(max_length=255, null=True, blank=True)
    intendedRecipientUserId = models.CharField(max_length=50, null=True, blank=True)
    sourceUserId = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self) -> str:
        return self.message if self.message else self.id
    
    


@receiver(post_save, sender=OutSourcedInfo)
def initialize_account(sender, instance, created, **kwargs):

    if created:
        account = Account()
        account.outsourced = instance
        account.save()
        print(f"initialized outsourced account - {instance}")



class OutreachTime(BaseModel):
    time_slot = models.DateTimeField()
    account_to_be_assigned = models.ForeignKey(Account,on_delete=models.CASCADE,null=True,blank=True)


class AccountsClosed(BaseModel):
    data = models.TextField(null=True,blank=True)

    def __str__(self) -> str:
        return self.data if self.data else self.id
    
class ExperimentStatus(BaseModel):
    name = models.CharField(null=False, blank=False,max_length=255, default='daft')
    description =  models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.lower()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name

    def get_id(self):
        return self.id

class ExperimentAssignee(BaseModel):
    name = models.CharField(null=False, blank=False,max_length=255, default='daft')
    description =  models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.lower()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name

    def get_id(self):
        return self.id

class Experiment(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True) # e.g Hypothesis
    hypothesis = models.TextField(blank=True)
    primary_metric = models.CharField(max_length=255)
    version = models.CharField(max_length=100, unique=True, blank=False, null=False)
    status = models.ForeignKey(ExperimentStatus, on_delete=models.CASCADE, null=False, blank=False)
    start_date = models.DateTimeField(null=True, blank=True)  # When the experiment starts
    end_date = models.DateTimeField(null=True, blank=True)  # When the experiment
    actual_result= models.FloatField(null=True, blank=True)  # The actual result of the experiment
    expected_result = models.FloatField(null=True, blank=True)  # The expected result of
    assignees = models.ManyToManyField('ExperimentAssignee', related_name='experiments', blank=True)
    experiment_type = models.CharField(max_length=255, null=False, blank=False, default='auto')

    def __str__(self):
        return self.version
    # Relationships to fixed models
    # engagement_script = models.ForeignKey(EngagementScript, on_delete=models.SET_NULL, null=True, blank=True)
    # prequalifying_criteria = models.ForeignKey(PrequalifyingCriteria, on_delete=models.SET_NULL, null=True, blank=True)
    

@receiver(pre_save, sender=Experiment)
def set_version_pre_save(sender, instance, **kwargs):
    if not instance.version:
        date_str = timezone.now().strftime("%m-%d-%Y@%H:%M:%S")
        instance.version = f"EXP-{date_str}"
        
    if not instance.status:
        instance.status = StatusCheck.objects.get(name="draft")

@receiver(post_save, sender=Experiment)
def update_actual_result_on_status_close(sender, instance, **kwargs):
    # only run for auto experiments
    if instance.experiment_type.lower() is 'manual':
        return
    # Only run this logic if status is "closed"
    closed_statuses = ['closed','evaluated']
    if instance.status.name.lower() not in closed_statuses:
        return
    
    # Ensure both dates are present
    if not instance.start_date or not instance.end_date:
        return
    
    if not instance.primary_metric:
        return

    # Normalize dates to avoid naive datetime issues
    start_date = instance.start_date
    end_date = instance.end_date
    primary_metric = instance.primary_metric.lower()
    
    # Fetch matching accounts
    matching_accounts_count = Account.objects.filter(
        status_param__iexact=primary_metric,
        outreach_time__gte=start_date,
        outreach_time__lte=end_date
    ).count()


    # Only update if the count is different
    if instance.actual_result != matching_accounts_count:
        instance.actual_result = matching_accounts_count
        instance.save(update_fields=['actual_result'])


    
class ExperimentFieldDefinition(BaseModel):
    """_summary_

    Args:
        BaseModel (_type_): _description_

    Raises:
        ValidationError: _description_
    is_input:
        Determines if this is an experiment input field
    is_result_field:
        Determines if this is an experiment result field
    is_metric:
        Determines if this field will be use for measurement
        
    The definition fields are those that are is_input == False and
    is_result_field == False
    Example input for config:
        {
            "name": "Impact",
            "field_type": "dropdown", # e.g dropdown, boolean, text, number, date etc
            "options": ["A","B","C"] #Required for dropdowns, radios etc
        }
            
    """
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name='field_definitions')
    config = models.JSONField(blank=False, null=False, ) # Frontend-defined form field metadata
    is_experiment_input = models.BooleanField(default=False)  # Used for experiment inputs e.g. account used like "barbersince98"
    is_metric_field = models.BooleanField(default=False)  # e.g. "Primary Metric"
    is_result_field = models.BooleanField(default=False)  # this marks it as a field for result entry
    value = models.JSONField(blank=True, null=True, )
    
class ExperimentFieldValue(BaseModel):
    # Example input for value
    # {"experiment_field_definition": ID, "value": "High"}
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name='field_values')
    field_definition = models.ForeignKey(ExperimentFieldDefinition, on_delete=models.CASCADE, related_name='field_values')
    value = models.JSONField()
 
class ExperimentInput(BaseModel):
    # Example input for value
    # {"experiment_field_definition": ID, "value": "High"}
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name='inputs')
    field = models.ForeignKey(ExperimentFieldDefinition, on_delete=models.CASCADE, related_name='inputs')
    value = models.TextField(blank=True)

    class Meta:
        unique_together = ('experiment', 'field')

    def __str__(self):
        return f"{self.field.label}: {self.value}"  

class ExperimentResult(BaseModel):
    # Example input for value
    # {"experiment_field_definition": ID, "value": "High"}
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name='results')
    field_definition = models.ForeignKey(ExperimentFieldDefinition, on_delete=models.CASCADE)
    value = models.JSONField(blank=True, null=True)
    
# class ExperimentResultFieldValue(models.Model):
#     result = models.ForeignKey(ExperimentResult, on_delete=models.CASCADE, related_name='result_values')
#     field_definition = models.ForeignKey(ExperimentFieldDefinition, on_delete=models.CASCADE)
#     value = models.JSONField(blank=True, null=True)