from django.contrib.contenttypes.admin import GenericTabularInline

from bluebottle.notifications.models import Message


class MessageAdminInline(GenericTabularInline):

    model = Message

    readonly_fields = ['sent', 'subject', 'recipient']
    fields = readonly_fields

    def has_add_permission(self, request):
        return False

    can_delete = False
