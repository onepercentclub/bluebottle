from django.contrib import admin

from bluebottle.analytics.models import AnalyticsPlatformSettings, AnalyticsAdapter
from bluebottle.utils.admin import BasePlatformSettingsAdmin


class AnalyticsAdapterInline(admin.TabularInline):
    model = AnalyticsAdapter
    extra = 0


class AnalyticsPlatformSettingsAdmin(BasePlatformSettingsAdmin):

    inlines = [AnalyticsAdapterInline]


admin.site.register(AnalyticsPlatformSettings, AnalyticsPlatformSettingsAdmin)
