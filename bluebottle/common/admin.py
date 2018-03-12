from bluebottle.common.models import CommonPlatformSettings
from django.contrib import admin
from django_singleton_admin.admin import SingletonAdmin


class CommonPlatformSettingsAdmin(SingletonAdmin):
    pass


admin.site.register(CommonPlatformSettings, CommonPlatformSettingsAdmin)
