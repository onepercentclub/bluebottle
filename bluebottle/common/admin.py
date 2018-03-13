from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html
from django_singleton_admin.admin import SingletonAdmin
from django.utils.translation import ugettext_lazy as _

from bluebottle.common.models import CommonPlatformSettings


class CommonPlatformSettingsAdmin(SingletonAdmin):

    readonly_fields = ('force_lockdown',)

    def get_fields(self, request, obj=None):
        if getattr(settings, 'FORCE_LOCKDOWN', False):
            return ('force_lockdown', 'lockdown_password')
        return ('lockdown', 'lockdown_password')

    def force_lockdown(self, obj):
        return format_html('<i>{}</i>', _('Lock-down is forced on this server.'))
    force_lockdown.short_description = 'Lockdown'


admin.site.register(CommonPlatformSettings, CommonPlatformSettingsAdmin)
