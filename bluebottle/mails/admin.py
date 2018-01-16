from django.contrib import admin

from django_singleton_admin.admin import SingletonAdmin

from bluebottle.mails.models import MailPlatformSettings


class MailPlatformSettingsAdmin(SingletonAdmin):
    pass


admin.site.register(MailPlatformSettings, MailPlatformSettingsAdmin)
