from django.contrib import admin

from django_singleton_admin.admin import SingletonAdmin

from bluebottle.mails.models import MailPlatformSettings, Mail


class MailPlatformSettingsAdmin(SingletonAdmin):
    pass


admin.site.register(MailPlatformSettings, MailPlatformSettingsAdmin)


class MailAdmin(admin.ModelAdmin):
    pass


admin.site.register(Mail, MailAdmin)
