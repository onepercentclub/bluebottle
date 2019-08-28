from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django_summernote.widgets import SummernoteWidget

from bluebottle.activities.admin import ActivityChildAdmin
from bluebottle.events.models import Event, Participant
from bluebottle.notifications.admin import MessageAdminInline
from bluebottle.utils.admin import FSMAdmin
from bluebottle.utils.forms import FSMModelForm


class EventAdminForm(FSMModelForm):

    class Meta:
        model = Event
        fields = '__all__'
        widgets = {
            'description': SummernoteWidget(attrs={'height': 200})
        }


class ParticipantInline(admin.TabularInline):
    model = Participant

    raw_id_fields = ('user', )
    readonly_fields = ('created', 'status', 'participant')
    fields = ('participant', 'user', 'created', 'status', 'time_spent')

    extra = 0

    def participant(self, obj):
        url = reverse('admin:events_participant_change', args=(obj.id,))
        return format_html('<a href="{}">{}</a>', url, obj.id)


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
    inlines = ActivityChildAdmin.inlines + (ParticipantInline, MessageAdminInline)
    list_display = ['title_display', 'status', 'review_status', 'start_date', 'start_time', 'duration']
    search_fields = ['title', 'description']

    base_model = Event

    readonly_fields = ActivityChildAdmin.readonly_fields
    raw_id_fields = ActivityChildAdmin.raw_id_fields + ['location']

    fieldsets = (
        (_('Basic'), {'fields': (
            'title', 'slug', 'initiative', 'owner',
            'status', 'transitions', 'review_status', 'review_transitions',
            'highlight', 'stats_data'
        )}),
        (_('Details'), {'fields': (
            'description', 'capacity',
            'start_date', 'start_time', 'duration', 'registration_deadline',
            'is_online', 'location', 'location_hint'
        )}),
    )
