from django.contrib import admin

from bluebottle.mails.models import MailPlatformSettings
from bluebottle.utils.admin import BasePlatformSettingsAdmin


class MailPlatformSettingsAdmin(BasePlatformSettingsAdmin):
    pass


admin.site.register(MailPlatformSettings, MailPlatformSettingsAdmin)
