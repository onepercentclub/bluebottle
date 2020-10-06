from django.contrib import admin

from bluebottle.analytics.models import AnalyticsPlatformSettings
from bluebottle.utils.admin import BasePlatformSettingsAdmin


@admin.register(AnalyticsPlatformSettings)
class AnalyticsPlatformSettingsAdmin(BasePlatformSettingsAdmin):
    pass
