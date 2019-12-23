from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django_summernote.widgets import SummernoteWidget

from bluebottle.activities.admin import ActivityChildAdmin, ContributionChildAdmin
from bluebottle.events.models import Event, Participant
from bluebottle.events.transitions import EventTransitions, ParticipantTransitions
from bluebottle.notifications.admin import MessageAdminInline
from bluebottle.utils.admin import export_as_csv_action
from bluebottle.utils.forms import FSMModelForm
from bluebottle.wallposts.admin import WallpostInline


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
class ParticipantAdmin(ContributionChildAdmin):
    model = Participant
    form = ParticipantAdminForm
    list_display = ['user', 'status', 'time_spent', 'activity_link']
    raw_id_fields = ('user', 'activity')

    export_to_csv_fields = (
        ('status', 'Status'),
        ('created', 'Created'),
        ('activity', 'Activity'),
        ('owner', 'Owner'),
        ('time_spent', 'Time Spent'),
    )

    actions = [export_as_csv_action(fields=export_to_csv_fields)]


@admin.register(Event)
class EventAdmin(ActivityChildAdmin):
    form = EventAdminForm
    inlines = ActivityChildAdmin.inlines + (ParticipantInline, MessageAdminInline, WallpostInline)
    list_display = [
        '__unicode__', 'initiative', 'status',
        'highlight', 'start_date', 'start_time', 'duration', 'created'
    ]
    search_fields = ['title', 'description']
    list_filter = ['status', 'is_online']
    date_hierarchy = 'start_date'

    base_model = Event

    readonly_fields = ActivityChildAdmin.readonly_fields
    raw_id_fields = ActivityChildAdmin.raw_id_fields + ['location']

    detail_fields = (
        'description',
        'capacity',
        'start_date',
        'start_time',
        'duration',
        'registration_deadline',
        'is_online',
        'location',
        'location_hint'
    )

    export_to_csv_fields = (
        ('title', 'Title'),
        ('description', 'Description'),
        ('status', 'Status'),
        ('created', 'Created'),
        ('initiative__title', 'Initiative'),
        ('start_date', 'Start Date'),
        ('start_time', 'Start Time'),
        ('duration', 'Duration'),
        ('end', 'End'),
        ('registration_deadline', 'Registration Deadline'),
        ('owner', 'Owner'),
        ('capacity', 'Capacity'),
        ('is_online', 'Will be hosted online?'),
        ('location', 'Location'),
        ('location_hint', 'Location Hint'),
        ('automatically_accept', 'Auto Accept Members'),
    )

    actions = [export_as_csv_action(fields=export_to_csv_fields)]

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            # If we created a new participant through admin then
            # set it to succeeded when event is succeeded
            if (instance.__class__ == Participant and
                    not instance.pk and
                    form.instance.status == EventTransitions.values.succeeded):
                instance.time_spent = form.instance.duration
                instance.status = ParticipantTransitions.values.succeeded
            instance.save()
        formset.save_m2m()
