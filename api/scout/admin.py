from django.contrib import admin
from .models import Scout,ScoutingMaster,Device
from django_tenants.utils import schema_context
from boostedchatScrapper.spiders.helpers.instagram_login_helper import login_user
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
import os

# Register your models here.


@admin.register(Scout)
class ScoutAdmin(admin.ModelAdmin):
    actions = ['check_scout_availability']
    @admin.action(description=_('Relogin Scouts'))
    def check_scout_availability(self, request, queryset):
        """
        Checks the availability of selected scouts by attempting to log them in.
        """
        with schema_context(os.getenv("SCHEMA_NAME")):
            updated_count = 0
            for scout in queryset:
                try:
                    client = login_user(scout)
                    scout.available = True
                    scout.save()
                    updated_count += 1
                except Exception as e:
                    print(e)
                    scout.available = False
                    scout.save()
                    updated_count += 1  # Count even if an exception occurred

            self.message_user(request, _(
                f'Successfully logged in {updated_count} scout(s).'
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
