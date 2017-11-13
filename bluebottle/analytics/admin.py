from django.contrib import admin

from django_singleton_admin.admin import SingletonAdmin

from bluebottle.analytics.models import AnalyticsPlatformSettings, AnalyticsAdapter


class AnalyticsAdapterInline(admin.TabularInline):
    model = AnalyticsAdapter
    extra = 0


class AnalyticsPlatformSettingsAdmin(SingletonAdmin):

    inlines = [AnalyticsAdapterInline]


admin.site.register(AnalyticsPlatformSettings, AnalyticsPlatformSettingsAdmin)
