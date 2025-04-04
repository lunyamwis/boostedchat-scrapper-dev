# Register your models here.
from django.contrib import admin

from .models import SalesRep, Influencer


@admin.register(SalesRep)
class SalesRepAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(SalesRepAdmin, self).get_form(request, obj, **kwargs)
        return form



@admin.register(Influencer)
class InfluencerAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(InfluencerAdmin, self).get_form(request, obj, **kwargs)
        return form
