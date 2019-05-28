from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from bluebottle.activities.admin import ActivityChildAdmin
from bluebottle.events.models import Event, Participant
from bluebottle.utils.admin import FSMAdmin
from bluebottle.utils.forms import FSMModelForm


class EventAdminForm(FSMModelForm):
    class Meta:
        model = Event
        fields = '__all__'


class ParticipantInline(admin.TabularInline):
    model = Participant

    raw_id_fields = ('user', )
    readonly_fields = ('created', 'status', )
    fields = ('user', 'created', 'status', 'time_spent')

    extra = 0

    def participant(self, obj):
        url = reverse('admin:events_participant_change', args=(obj.id,))
        return format_html('<a href="{}">{}</a>', url, obj.user)


class ParticipantAdminForm(FSMModelForm):
    class Meta:
        model = Participant
        exclude = ['status', ]


@admin.register(Participant)
class ParticipantAdmin(FSMAdmin):
    model = Participant
    form = ParticipantAdminForm
    list_display = ['user', 'status', 'time_spent']
    raw_id_fields = ('user', 'activity')


@admin.register(Event)
class EventAdmin(ActivityChildAdmin):
    form = EventAdminForm
    inlines = ActivityChildAdmin.inlines + (ParticipantInline, )
    list_display = ['title', 'status', 'start_time', 'end_time']
    base_model = Event
