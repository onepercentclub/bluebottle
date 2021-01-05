from django.contrib import admin
from django.db import models
from django.db.models import Sum
from django.forms import Textarea
from django.template import loader
from django.urls import reverse, resolve
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django_summernote.widgets import SummernoteWidget
from bluebottle.utils.widgets import TimeDurationWidget, get_human_readable_duration

from bluebottle.activities.admin import ActivityChildAdmin, ContributorChildAdmin, ContributionChildAdmin
from bluebottle.fsm.admin import StateMachineFilter, StateMachineAdmin
from bluebottle.notifications.admin import MessageAdminInline
from bluebottle.time_based.models import (
    DateActivity, PeriodActivity, DateParticipant, PeriodParticipant, Participant, TimeContribution, DateActivitySlot
)
from bluebottle.utils.admin import export_as_csv_action
from bluebottle.fsm.forms import StateMachineModelForm


class BaseParticipantAdminInline(admin.TabularInline):
    model = Participant
    readonly_fields = ('contributor_date', 'motivation', 'document', 'edit', 'created', 'transition_date', 'status')
    raw_id_fields = ('user', 'document')
    extra = 0

    def get_parent_object_from_request(self, request):
        """
        Returns the parent object from the request or None.

        Note that this only works for Inlines, because the `parent_model`
        is not available in the regular admin.ModelAdmin as an attribute.
        """
        resolved = resolve(request.path_info)
        if resolved.args:
            return self.parent_model.objects.get(pk=resolved.args[0])
        return None

    def edit(self, obj):
        if not obj.id:
            return '-'
        return format_html(
            '<a href="{}">{}</a>',
            reverse(
                'admin:time_based_{}_change'.format(obj.__class__.__name__.lower()),
                args=(obj.id,)),
            _('Edit participant')
        )

    def has_add_permission(self, request):
        activity = self.get_parent_object_from_request(request)
        if not activity or activity.status in ['draft', 'needs_work']:
            return False
        return True


class DateParticipantAdminInline(BaseParticipantAdminInline):
    model = DateParticipant
    verbose_name = _("Participant")
    verbose_name_plural = _("Participants")
    readonly_fields = BaseParticipantAdminInline.readonly_fields
    fields = ('edit', 'user', 'status')


class PeriodParticipantAdminInline(BaseParticipantAdminInline):
    model = PeriodParticipant
    verbose_name = _("Participant")
    verbose_name_plural = _("Participants")
    fields = ('edit', 'user', 'status')


class TimeBasedAdmin(ActivityChildAdmin):
    inlines = ActivityChildAdmin.inlines + (MessageAdminInline, )

    formfield_overrides = {
        models.DurationField: {
            'widget': TimeDurationWidget(
                show_days=False,
                show_hours=True,
                show_minutes=True,
                show_seconds=False)
        },
        models.TextField: {
            'widget': Textarea(
                attrs={
                    'rows': 3,
                    'cols': 80
                }
            )
        },
    }

    search_fields = ['title', 'description']
    list_filter = [StateMachineFilter, 'is_online']

    raw_id_fields = ActivityChildAdmin.raw_id_fields + ['location']

    export_to_csv_fields = (
        ('title', 'Title'),
        ('description', 'Description'),
        ('status', 'Status'),
        ('created', 'Created'),
        ('initiative__title', 'Initiative'),
        ('registration_deadline', 'Registration Deadline'),
        ('owner__full_name', 'Owner'),
        ('owner__email', 'Email'),
        ('capacity', 'Capacity'),
        ('is_online', 'Will be hosted online?'),
        ('location', 'Location'),
        ('location_hint', 'Location Hint'),
        ('review', 'Review participants')
    )

    def duration_string(self, obj):
        duration = get_human_readable_duration(str(obj.duration)).lower()
        if not obj.duration_period or obj.duration_period != 'overall':
            return _('{duration} per {time_unit}').format(
                duration=duration,
                time_unit=obj.duration_period[0:-1])
        return duration
    duration_string.short_description = _('Duration')


class TimeBasedActivityAdminForm(StateMachineModelForm):

    class Meta(object):
        model = PeriodActivity
        fields = '__all__'
        widgets = {
            'description': SummernoteWidget(attrs={'height': 400})
        }


class DateActivityASlotInline(admin.TabularInline):
    model = DateActivitySlot

    readonly_fields = [
        'duration',
        'link'
    ]

    fields = [
        'link',
        'start',
        'duration'
    ]

    extra = 0

    def link(self, obj):
        url = reverse('admin:time_based_dateactivityslot_change', args=(obj.id,))
        return format_html('<a href="{}">{}</a>', url, obj)


@admin.register(DateActivity)
class DateActivityAdmin(TimeBasedAdmin):
    base_model = DateActivity
    form = TimeBasedActivityAdminForm
    inlines = (DateActivityASlotInline, DateParticipantAdminInline,) + TimeBasedAdmin.inlines

    raw_id_fields = ActivityChildAdmin.raw_id_fields + ['location']
    list_filter = TimeBasedAdmin.list_filter + ['expertise']

    date_hierarchy = 'start'
    list_display = TimeBasedAdmin.list_display + [
        'start',
        'duration_string',
    ]

    detail_fields = ActivityChildAdmin.detail_fields + (
        'start',
        'duration',

        'preparation',
        'registration_deadline',

        'is_online',
        'location',
        'location_hint',
        'online_meeting_url',

        'expertise',
        'capacity',
        'review',

    )

    export_as_csv_fields = TimeBasedAdmin.export_to_csv_fields + (
        ('start', 'Start'),
        ('duration', 'TimeContribution'),
    )
    actions = [export_as_csv_action(fields=export_as_csv_fields)]


@admin.register(PeriodActivity)
class PeriodActivityAdmin(TimeBasedAdmin):
    base_model = PeriodActivity

    inlines = (PeriodParticipantAdminInline,) + TimeBasedAdmin.inlines

    form = TimeBasedActivityAdminForm
    list_filter = TimeBasedAdmin.list_filter + ['expertise']

    date_hierarchy = 'deadline'
    list_display = TimeBasedAdmin.list_display + [
        'start', 'end_date', 'duration_string'
    ]

    detail_fields = ActivityChildAdmin.detail_fields + (
        'start',
        'deadline',
        'registration_deadline',

        'duration',
        'duration_period',
        'preparation',

        'is_online',
        'location',
        'location_hint',
        'online_meeting_url',

        'expertise',
        'capacity',
        'review',
    )

    export_as_csv_fields = TimeBasedAdmin.export_to_csv_fields + (
        ('deadline', 'Deadline'),
        ('duration', 'TimeContribution'),
        ('duration_period', 'TimeContribution period'),
    )
    actions = [export_as_csv_action(fields=export_as_csv_fields)]

    def end_date(self, obj):
        if not obj.deadline:
            return _('indefinitely')
        return obj.deadline


class SlotAdmin(StateMachineAdmin):

    formfield_overrides = {
        models.DurationField: {
            'widget': TimeDurationWidget(
                show_days=False,
                show_hours=True,
                show_minutes=True,
                show_seconds=False)
        },
        models.TextField: {
            'widget': Textarea(
                attrs={
                    'rows': 3,
                    'cols': 80
                }
            )
        },
    }

    def duration_string(self, obj):
        duration = get_human_readable_duration(str(obj.duration)).lower()
        return duration
    duration_string.short_description = _('Duration')

    def valid(self, obj):
        errors = list(obj.errors)
        required = list(obj.required)
        if not errors and obj.states.initiative_is_approved() and not required:
            return '-'

        errors += [
            _("{} is required").format(obj._meta.get_field(field).verbose_name.title())
            for field in required
        ]

        template = loader.get_template(
            'admin/validation_steps.html'
        )
        return template.render({'errors': errors})

    valid.short_description = _('Validation')

    readonly_fields = [
        'created',
        'updated',
        'valid'
    ]
    detail_fields = []
    status_fields = [
        'status',
        'states',
        'created',
        'updated'
    ]

    def get_status_fields(self, request, obj):
        fields = self.status_fields
        if obj and obj.status in ('draft', ):
            fields = ['valid'] + fields

        return fields

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (_('Detail'), {'fields': self.detail_fields}),
            (_('Status'), {'fields': self.get_status_fields(request, obj)}),
        )
        if request.user.is_superuser:
            fieldsets += (
                (_('Super admin'), {'fields': (
                    'force_status',
                )}),
            )
        return fieldsets


@admin.register(DateActivitySlot)
class DateSlotAdmin(SlotAdmin):
    model = DateActivity

    # inlines = (DateSeesionParticipantInlines,)

    raw_id_fields = ['activity', 'location']
    # list_filter = ['expertise']

    date_hierarchy = 'start'
    list_display = [
        '__str__', 'start', 'duration_string',
    ]

    detail_fields = SlotAdmin.detail_fields + [
        'activity',
        'start',
        'duration',
        'is_online',
        'location',
        'location_hint',
        'online_meeting_url',
    ]


class TimeContributionInlineAdmin(admin.TabularInline):
    model = TimeContribution
    extra = 0
    readonly_fields = ('edit', 'status', )
    fields = readonly_fields + ('start', 'value')

    formfield_overrides = {
        models.DurationField: {
            'widget': TimeDurationWidget(
                show_days=False,
                show_hours=True,
                show_minutes=True,
                show_seconds=False)
        }
    }

    def edit(self, obj):
        if not obj.id:
            return '-'
        return format_html(
            '<a href="{}">{}</a>',
            reverse(
                'admin:time_based_{}_change'.format(obj.__class__.__name__.lower()),
                args=(obj.id,)),
            _('Edit duration')
        )


@admin.register(PeriodParticipant)
class PeriodParticipantAdmin(ContributorChildAdmin):
    inlines = ContributorChildAdmin.inlines + [TimeContributionInlineAdmin]
    readonly_fields = ContributorChildAdmin.readonly_fields + ['total']
    fields = ContributorChildAdmin.fields + ['total', 'motivation', 'current_period', 'document']

    def total(self, obj):
        if not obj:
            return '-'
        return obj.contributions.aggregate(total=Sum('timecontribution__value'))['total']
    total.short_description = _('Total contributed')


@admin.register(TimeContribution)
class TimeContributionAdmin(ContributionChildAdmin):
    fields = ['contributor', 'created', 'start', 'end', 'value', 'status', 'states']


@admin.register(DateParticipant)
class DateParticipantAdmin(ContributorChildAdmin):
    inlines = ContributorChildAdmin.inlines + [TimeContributionInlineAdmin]
    fields = ContributorChildAdmin.fields + ['motivation', 'document']
