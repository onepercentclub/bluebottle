from django.contrib import admin

from bluebottle.events.models import Event, Webhook
from bluebottle.fsm.admin import StateMachineAdmin


@admin.register(Event)
class EventAdmin(StateMachineAdmin, admin.ModelAdmin):
    list_display = ('id', 'content_type', 'event_type', 'created',)
    ordering = ('-created',)
    readonly_fields = ('id', 'created', 'updated')


@admin.register(Webhook)
class WebHookAdmin(admin.ModelAdmin):
    list_display = ('id', 'url', )
