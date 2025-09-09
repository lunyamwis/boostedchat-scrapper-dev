from django.contrib import admin
from .models import ExperimentAssignee, ExperimentStatus, InstagramUser,LeadSource,QualificationAlgorithm,Scheduler,Score,Account, Message, OutSourced, Photo, StatusCheck, Thread, Video,OutreachTime,AccountsClosed, UnwantedAccount, Comment, Like

# Register your models here.
# Register your models here.
import json
import os
import logging

from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import DateFieldListFilter
from django_tenants.utils import schema_context  # or your schema context utility
from django.contrib import messages
from django.db.models import Count

from .models import Account, Message, OutSourced, Photo, StatusCheck, Thread, Video,OutreachTime,AccountsClosed, UnwantedAccount, Comment, Like
from api.prompt.models import Department

admin.site.register(Photo)
admin.site.register(Video)

from django.http import HttpResponseRedirect
from django.urls import reverse
from .utils import get_the_cut_info  # Import your function
from api.workflow.tasks import send_first_compliment,qualify_and_reschedule, send_test_compliment, delete_accounts, remove_duplicates_task

@admin.action(description='Get The Cut Info')
def get_cut_info_action(modeladmin, request, queryset):
    for obj in queryset:
        # Call your function for each selected object
        outsourced = obj.outsourced_set.get(account__id=obj.id)
        print(outsourced.results.get("external_url"))
        the_cut_username = outsourced.results.get("external_url").split('/')[-1]
        print(the_cut_username)
        info = get_the_cut_info(the_cut_username)
        # Do something with the info, for example, update a field
        obj.referral = json.dumps(info)
        obj.save()
    

    # Redirect to the admin page after the action is done
    return HttpResponseRedirect(reverse('admin:app_list', args=('instagram',)))

@admin.action(description='Qualify in batch')
def set_qualified_true_action(modeladmin, request, queryset):
    # Iterate over the selected objects in the queryset
    for obj in queryset:
        # Set the qualified attribute to True
        obj.qualified = True
        # Save the changes to the database
        obj.save()

    # Redirect to the admin page after the action is done
    return HttpResponseRedirect(reverse('admin:app_list', args=('instagram',)))


@admin.action(description='Disqualify in batch')
def set_disqualified_true_action(modeladmin, request, queryset):
    # Iterate over the selected objects in the queryset
    for obj in queryset:
        # Set the qualified attribute to True
        obj.qualified = False
        # Save the changes to the database
        obj.save()

    # Redirect to the admin page after the action is done
    return HttpResponseRedirect(reverse('admin:app_list', args=('instagram',)))

class YesterdayFilter(DateFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        super().__init__(field, request, params, model, model_admin, field_path)
        yesterday = timezone.now().date() - timezone.timedelta(days=1)
        tomorrow = timezone.now().date() + timezone.timedelta(days=1)
        today = timezone.now().date()
        self.links += (
            (_('Added from yesterday'), {
                self.field_path + '__gte': yesterday.strftime('%Y-%m-%d'),
                self.field_path + '__lt': tomorrow.strftime('%Y-%m-%d'),
            }),
            (_('Added for tomorrow'), {
                self.field_path + '__gte': today.strftime('%Y-%m-%d'),
                self.field_path + '__lt': (tomorrow + timezone.timedelta(days=1)).strftime('%Y-%m-%d'),
            })
        )
        
class TomorrowFilter(DateFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        super().__init__(field, request, params, model, model_admin, field_path)
        tomorrow = timezone.now() + timezone.timedelta(days=1)
        self.links += (
            (_('Added for tomorrow'), {
                self.field_path + '__gte': tomorrow.strftime('%Y-%m-%d'),
                self.field_path + '__lt': (tomorrow + timezone.timedelta(days=1)).strftime('%Y-%m-%d'),
            }),
        )

class StatusFilter(admin.SimpleListFilter):
    title = _("Status")  # Display name in the admin filter sidebar
    parameter_name = "status"  # Query parameter in the URL

    def lookups(self, request, model_admin):
        """Defines filter choices in the sidebar."""
        statuses = StatusCheck.objects.all()
        status_options = [(status.id, status.name) for status in statuses]

        # Add extra options for NULL filtering
        status_options.insert(0, ("null", _("No Status (NULL)")))
        status_options.insert(1, ("not_null", _("Has Status")))

        return status_options

    def queryset(self, request, queryset):
        """Filters the queryset based on the selected value."""
        if self.value() == "null":
            return queryset.filter(status__isnull=True)  # Show only accounts with NULL status
        elif self.value() == "not_null":
            return queryset.filter(status__isnull=False)  # Show only accounts with a status
        elif self.value():
            return queryset.filter(status_id=self.value())  # Filter by specific status ID
        return queryset  # Default: No filtering



class UnscheduledFilter(admin.SimpleListFilter):
    title = _('Unscheduled')  # Display title in the admin filter sidebar
    parameter_name = 'outreach_time_null'  # Query parameter in the URL

    def lookups(self, request, model_admin):
        """Defines filter choices in the sidebar."""
        return [
            ('yes', _('Unscheduled')),  # Option to filter accounts with outreach_time null
        ]

    def queryset(self, request, queryset):
        """Applies filtering logic."""
        # today = timezone.now().date()  # Get today's date
        yesterday = timezone.now().date() - timezone.timedelta(days=1)
        if self.value() == 'yes':
            return queryset.filter(outreach_time__isnull=True,created_at__date__gt=yesterday)  # Filter where outreach_time is NULL
        return queryset
    
  

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    search_fields = ['igname__icontains']
    actions = [get_cut_info_action, set_qualified_true_action, set_disqualified_true_action,
               'send_compliment','send_test_compliment','qualify_reschedule','use_latest_prompt','use_previous_prompt',
               'remove_duplicates']
    
    list_filter = [
        'qualified',  # Filter for unqualified accounts
        ('created_at', YesterdayFilter),  # Custom filter for created_at
        UnscheduledFilter,  # New filter for outreach_time NULL
        StatusFilter,
        'dormant_profile_created',
    ]

    @admin.action(description=_('Send Test Compliment'))
    def send_test_compliment(self, request, queryset):
        """
        Checks the availability of selected scouts by attempting to log them in.
        """
        # Get the list of selected scout IDs

        selected_instagram_account = queryset.values_list('igname', flat=True)
        print(selected_instagram_account)
        send_test_compliment.delay(username=list(selected_instagram_account), message="")
        self.message_user(request, _(
            f'Successfully sending test compliment.'
        ), messages.INFO)

    send_test_compliment.short_description = _('Send Test Compliment')

    @admin.action(description=_('Send Compliment'))
    def send_compliment(self, request, queryset):
        """
        Checks the availability of selected scouts by attempting to log them in.
        """
        # Get the list of selected scout IDs

        selected_instagram_account = queryset.values_list('igname', flat=True)
        print(selected_instagram_account)
        send_first_compliment.delay(username=list(selected_instagram_account),message="")
        self.message_user(request, _(
            f'Successfully sending compliment.'
        ), messages.INFO)

    send_compliment.short_description = _('Send Compliment')

    @admin.action(description=_('Use latest prompt version'))
    def use_latest_prompt(self, request, queryset):
        """
        Checks the availability of selected scouts by attempting to log them in.
        """
        # Get the list of selected scout IDs

        for account in queryset:
            account.engagement_version = Department.objects.filter(name="Engagement Department").latest("version").version
            account.save()
        logging.warning(f"Latest prompt version {Department.objects.filter(name='Engagement Department').latest('version').version} assigned to {queryset.count()} accounts.")
        self.message_user(request, _(
            f'Successfully assigned to latest prompt.'
        ), messages.INFO)

    use_latest_prompt.short_description = _('Use latest prompt version')

    @admin.action(description=_('Use previous prompt version'))
    def use_previous_prompt(self, request, queryset):
        """
        Checks the availability of selected scouts by attempting to log them in.
        """
        # Get the list of selected scout IDs

        for account in queryset:
            account.engagement_version = str(int(Department.objects.filter(name="Engagement Department").latest("version").version) - 1)
            account.save()
        logging.warning(f"Previous prompt version set ")
        self.message_user(request, _(
            f'Successfully assigned to previous prompt.'
        ), messages.INFO)

    use_previous_prompt.short_description = _('Use previous prompt version')

    @admin.action(description=_('Qualify and Reschedule'))
    def qualify_reschedule(self, request, queryset):
        """
        Checks the availability of selected scouts by attempting to log them in.
        """
        # Get the list of selected scout IDs

        qualify_and_reschedule.delay()
        self.message_user(request, _(
            f'Successfully qualifying and rescheduling.'
        ), messages.INFO)

    qualify_reschedule.short_description = _('Qualify and Reschedule')

    @admin.action(description=_('Remove Duplicates'))
    def remove_duplicates(self, request, queryset):
        remove_duplicates_task.delay()

        self.message_user(request, _(
            f'Successfully removed duplicates.'
        ), messages.INFO)

    remove_duplicates.short_description = _('Remove Duplicates')

    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(AccountAdmin, self).get_form(request, obj, **kwargs)
        return form

    
class RecentAccountsFilter(admin.SimpleListFilter):
    title = _('Recent Accounts')  # Displayed in the admin sidebar
    parameter_name = 'recent_accounts'  # URL parameter for the filter

    def lookups(self, request, model_admin):
        # Define the filter options
        return (
            ('recent', _('Added from yesterday')),
        )

    def queryset(self, request, queryset):
        # Apply the filter logic
        if self.value() == 'recent':
            yesterday = timezone.now() - timezone.timedelta(days=1)
            return queryset.filter(outreach_time__gte=yesterday)
        return queryset


class UnqualifiedAccountsFilter(admin.SimpleListFilter):
    title = _('Unqualified Accounts')  # Displayed in the admin sidebar
    parameter_name = 'unqualified_accounts'  # URL parameter for the filter

    def lookups(self, request, model_admin):
        # Define the filter options
        return (
            ('unqualified', _('Unqualified Accounts')),
        )

    def queryset(self, request, queryset):
        # Apply the filter logic
        if self.value() == 'unqualified':
            return queryset.filter(qualified=False)
        return queryset

@admin.register(OutreachTime)
class OutreachTimeAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(OutreachTimeAdmin, self).get_form(request, obj, **kwargs)
        return form

@admin.register(StatusCheck)
class StatusAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(StatusAdmin, self).get_form(request, obj, **kwargs)
        return form


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(ThreadAdmin, self).get_form(request, obj, **kwargs)
        return form

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(MessageAdmin, self).get_form(request, obj, **kwargs)
        return form


@admin.register(OutSourced)
class OutSourcedAdmin(admin.ModelAdmin):
    search_fields = ['account__igname__icontains',]
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(OutSourcedAdmin, self).get_form(request, obj, **kwargs)
        return form



@admin.register(AccountsClosed)
class AccountsClosedAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(AccountsClosedAdmin, self).get_form(request, obj, **kwargs)
        return form



@admin.register(UnwantedAccount)
class UnwantedAccountAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(UnwantedAccountAdmin, self).get_form(request, obj, **kwargs)
        return form
    

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(CommentAdmin, self).get_form(request, obj, **kwargs)
        return form


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(LikeAdmin, self).get_form(request, obj, **kwargs)
        return form


@admin.register(LeadSource)
class LeadSourceAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(LeadSourceAdmin, self).get_form(request, obj, **kwargs)
        return form

@admin.register(QualificationAlgorithm)
class QualificationAlgorithmAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(QualificationAlgorithmAdmin, self).get_form(request, obj, **kwargs)
        return form
    
@admin.register(Scheduler)
class SchedulerAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(SchedulerAdmin, self).get_form(request, obj, **kwargs)
        return form

@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(ScoreAdmin, self).get_form(request, obj, **kwargs)
        return form
    

@admin.register(InstagramUser)
class InstagramUserAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(InstagramUserAdmin, self).get_form(request, obj, **kwargs)
        return form

@admin.register(ExperimentAssignee)
class ExperimentAssigneeAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(ExperimentAssigneeAdmin, self).get_form(request, obj, **kwargs)
        return form
    
@admin.register(ExperimentStatus)
class ExperimentStatusAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(ExperimentStatusAdmin, self).get_form(request, obj, **kwargs)
        return form
