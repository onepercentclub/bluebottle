from django.contrib import admin

from bluebottle.mails.models import MailPlatformSettings
from bluebottle.utils.admin import BasePlatformSettingsAdmin


@admin.register(MailPlatformSettings)
class MailPlatformSettingsAdmin(BasePlatformSettingsAdmin):
    pass
