from builtins import object
from django.contrib import admin
from django_summernote.widgets import SummernoteWidget

from bluebottle.fsm.admin import StateMachineFilter
from bluebottle.activities.admin import ActivityChildAdmin, ContributorChildAdmin, ContributorInline
from bluebottle.events.models import Event, Participant
from bluebottle.notifications.admin import MessageAdminInline
from bluebottle.utils.admin import export_as_csv_action
from bluebottle.fsm.forms import StateMachineModelForm


class EventAdminForm(StateMachineModelForm):

    class Meta(object):
        model = Event
        fields = '__all__'
        widgets = {
            'description': SummernoteWidget(attrs={'height': 200})
        }


class ParticipantInline(ContributorInline):
    model = Participant

    readonly_fields = ContributorInline.readonly_fields + ('time_spent', )
    fields = ContributorInline.fields + ('time_spent', )


class ParticipantAdminForm(StateMachineModelForm):
    class Meta(object):
        model = Participant
        exclude = ('transition_date', )


@admin.register(Participant)
class ParticipantAdmin(ContributorChildAdmin):
    model = Participant
    form = ParticipantAdminForm
    list_display = ['user', 'state_name', 'time_spent', 'activity_link']
    raw_id_fields = ('user', 'activity')

    readonly_fields = ContributorChildAdmin.readonly_fields
    fields = ContributorChildAdmin.fields + ['time_spent']

    date_hierarchy = 'transition_date'

    export_to_csv_fields = (
        ('status', 'Status'),
        ('created', 'Created'),
        ('activity', 'Activity'),
        ('user__full_name', 'Owner'),
        ('user__email', 'Email'),
        ('time_spent', 'Time Spent'),
        ('contributor_date', 'Contributor Date'),
    )

    actions = [export_as_csv_action(fields=export_to_csv_fields)]


@admin.register(Event)
class EventAdmin(ActivityChildAdmin):
    form = EventAdminForm
    inlines = ActivityChildAdmin.inlines + (ParticipantInline, MessageAdminInline)
    list_display = [
        '__str__', 'initiative', 'state_name',
        'highlight', 'start', 'duration', 'created'
    ]
    search_fields = ['title', 'description']
    list_filter = [StateMachineFilter, 'is_online']
    date_hierarchy = 'start'

    base_model = Event

    readonly_fields = ActivityChildAdmin.readonly_fields + ['local_start', ]
    raw_id_fields = ActivityChildAdmin.raw_id_fields + ['location']

    detail_fields = (
        'description',
        'capacity',
        'start',
        'local_start',
        'duration',
        'registration_deadline',
        'is_online',
        'online_meeting_url',
        'location',
        'location_hint',
        'highlight',
    )

    export_to_csv_fields = (
        ('title', 'Title'),
        ('description', 'Description'),
        ('status', 'Status'),
        ('created', 'Created'),
        ('initiative__title', 'Initiative'),
        ('start', 'Start'),
        ('duration', 'TimeContribution'),
        ('end', 'End'),
        ('registration_deadline', 'Registration Deadline'),
        ('owner__full_name', 'Owner'),
        ('owner__email', 'Email'),
        ('capacity', 'Capacity'),
        ('is_online', 'Will be hosted online?'),
        ('location', 'Location'),
        ('location_hint', 'Location Hint'),
    )

    actions = [export_as_csv_action(fields=export_to_csv_fields)]
