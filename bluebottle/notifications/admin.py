from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from bluebottle.notifications.models import Message, NotificationPlatformSettings
from bluebottle.utils.admin import BasePlatformSettingsAdmin


class MessageAdminInline(GenericTabularInline):

    model = Message

    readonly_fields = ['sent', 'subject', 'recipient']
    fields = readonly_fields

    def has_add_permission(self, request):
        return False

    extra = 0

    can_delete = False


@admin.register(NotificationPlatformSettings)
class NotificationPlatformSettingsAdmin(BasePlatformSettingsAdmin):
    pass
