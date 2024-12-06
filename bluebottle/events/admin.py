from django.contrib import admin

from bluebottle.events.models import Event
from bluebottle.fsm.admin import StateMachineAdmin


@admin.register(Event)
class EventAdmin(StateMachineAdmin, admin.ModelAdmin):
    list_display = ('id', 'type', 'created',)
    ordering = ('-created',)
    readonly_fields = ('id', 'type', 'created', 'updated')
