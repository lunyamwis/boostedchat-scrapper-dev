from django.contrib import admin
from .models import Scout,ScoutingMaster,Device
from django_tenants.utils import schema_context
from boostedchatScrapper.spiders.helpers.instagram_login_helper import login_user
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from api.workflow.tasks import relogin_scouts
import os

# Register your models here.


@admin.register(Scout)
class ScoutAdmin(admin.ModelAdmin):
    actions = ['check_scout_availability']
    search_fields = ['username__icontains']
    list_filter = [
        'available', 
        'country', 
        'city'
    ]
    @admin.action(description=_('Relogin Scouts'))
    def check_scout_availability(self, request, queryset):
        """
        Checks the availability of selected scouts by attempting to log them in.
        """
        # Get the list of selected scout IDs

        selected_scouts = queryset.values_list('id', flat=True)
        print(selected_scouts)
        relogin_scouts.delay(list(selected_scouts))
        self.message_user(request, _(
            f'Successfully logging in scout(s).'
        ), messages.INFO)

    check_scout_availability.short_description = _('Relogin Scouts')
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(ScoutAdmin, self).get_form(request, obj, **kwargs)
        return form

@admin.register(ScoutingMaster)
class ScoutingMasterAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(ScoutingMasterAdmin, self).get_form(request, obj, **kwargs)
        return form
    
@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(DeviceAdmin, self).get_form(request, obj, **kwargs)
        return form
