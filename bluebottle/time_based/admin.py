from django import forms
from django.conf.urls import url
from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter, widgets
from django.db import models
from django.forms import BaseInlineFormSet, BooleanField, ModelForm, Textarea, TextInput
from django.http import HttpResponseRedirect
from django.template import defaultfilters, loader
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html
from django.utils.timezone import get_current_timezone, now
from django.utils.translation import gettext_lazy as _
from django_admin_inline_paginator.admin import TabularInlinePaginated
from django_summernote.widgets import SummernoteWidget
from inflection import ordinalize
from parler.admin import SortedRelatedFieldListFilter, TranslatableAdmin
from polymorphic.admin import PolymorphicChildModelAdmin, PolymorphicInlineSupportMixin, PolymorphicParentModelAdmin, \
    PolymorphicChildModelFilter
from pytz import timezone

from bluebottle.activities.admin import (
    ActivityChildAdmin,
    ActivityForm,
    ContributionChildAdmin,
    ContributorChildAdmin, BaseContributorInline,
)
from bluebottle.files.fields import PrivateDocumentModelChoiceField
from bluebottle.files.widgets import DocumentWidget
from bluebottle.fsm.admin import StateMachineAdmin, StateMachineFilter
from bluebottle.geo.models import Location
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.notifications.admin import MessageAdminInline
from bluebottle.segments.models import SegmentType
from bluebottle.time_based.models import (
    DateActivity,
    DateActivitySlot,
    DateParticipant,
    DeadlineActivity,
    DeadlineParticipant,
    DeadlineRegistration,
    PeriodicActivity,
    PeriodicParticipant,
    PeriodicRegistration,
    ScheduleSlot,
    Skill,
    SlotParticipant,
    TimeContribution, Registration, PeriodicSlot, ScheduleActivity, ScheduleParticipant, ScheduleRegistration,
)
from bluebottle.time_based.states import SlotParticipantStateMachine
from bluebottle.time_based.utils import bulk_add_participants
from bluebottle.time_based.utils import duplicate_slot, nth_weekday
from bluebottle.utils.admin import TranslatableAdminOrderingMixin, export_as_csv_action
from bluebottle.utils.widgets import TimeDurationWidget, get_human_readable_duration


class DateParticipantAdminInline(BaseContributorInline):
    model = DateParticipant
    verbose_name = _("Participant")
    verbose_name_plural = _("Participants")


class TimeBasedAdmin(ActivityChildAdmin):
    inlines = ActivityChildAdmin.inlines + (MessageAdminInline,)

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
    list_filter = [StateMachineFilter]

    raw_id_fields = ActivityChildAdmin.raw_id_fields + ['expertise']

    export_to_csv_fields = (
        ('title', 'Title'),
        ('description', 'Description'),
        ('status', 'Status'),
        ('created', 'Created'),
        ('initiative__title', 'Initiative'),
        ('registration_deadline', 'Registration Deadline'),
        ('owner__full_name', 'Owner'),
        ('owner__email', 'Email'),
        ('office_location', 'Office Location'),
        ('capacity', 'Capacity'),
        ('review', 'Review participants')
    )

    def duration_string(self, obj):
        duration = get_human_readable_duration(str(obj.duration)).lower()
        if obj.duration_period and obj.duration_period != 'overall':
            return _('{duration} per {time_unit}').format(
                duration=duration,
                time_unit=obj.duration_period[0:-1])
        return duration

    duration_string.short_description = _('Duration')

    detail_fields = (
        'title',
        'description',
        'image',
        'video_url'
    )

    status_fields = (
        'initiative',
        'owner',
        'slug',
        'highlight',
        'created',
        'updated',
        'has_deleted_data',
        'status',
        'states',
    )

    registration_fields = (
        'expertise',
        'review',
        'registration_flow',
        'review_title',
        'review_description',
        'review_document_enabled',
        'review_link',
        'preparation',
        'registration_deadline',
    )

    def get_registration_fields(self, request, obj):
        return self.registration_fields

    def get_fieldsets(self, request, obj=None):
        settings = InitiativePlatformSettings.objects.get()
        fieldsets = [
            (_("Management"), {"fields": self.get_status_fields(request, obj)}),
            (_("Information"), {"fields": self.get_detail_fields(request, obj)}),
            (
                _("Participation"),
                {"fields": self.get_registration_fields(request, obj)},
            ),
        ]

        if Location.objects.count():
            if settings.enable_office_restrictions:
                if 'office_restriction' not in self.office_fields:
                    self.office_fields += (
                        'office_restriction',
                    )
            fieldsets.insert(2, (
                _('Office'), {'fields': self.office_fields}
            ))

        if request.user.is_superuser:
            fieldsets += [
                (_('Super admin'), {'fields': (
                    'force_status',
                )}),
            ]

        if SegmentType.objects.count():
            fieldsets.insert(4, (
                _('Segments'), {
                    'fields': [
                        segment_type.field_name
                        for segment_type in SegmentType.objects.all()
                    ]
                }
            ))
        return fieldsets

    def participant_count(self, obj):
        return obj.succeeded_contributor_count

    participant_count.short_description = _("Participants")


class TimeBasedActivityAdminForm(ActivityForm):
    class Meta(object):
        fields = '__all__'
        model = PeriodicActivity
        widgets = {
            'description': SummernoteWidget(attrs={'height': 400})
        }


class DateActivitySlotInline(TabularInlinePaginated):
    model = DateActivitySlot
    per_page = 20
    can_delete = True

    formfield_overrides = {
        models.DurationField: {
            'widget': TimeDurationWidget(
                show_days=False,
                show_hours=True,
                show_minutes=True,
                show_seconds=False)
        },
    }
    ordering = ['-start']
    readonly_fields = ['link', 'timezone', ]
    fields = [
        'link',
        'title',
        'start',
        'timezone',
        'duration',
        'is_online',
    ]

    extra = 0

    def link(self, obj):
        url = reverse('admin:time_based_dateactivityslot_change', args=(obj.id,))
        return format_html('<a href="{}">{}</a>', url, obj)

    def timezone(self, obj):
        if not obj.is_online and obj.location:
            return f'{obj.start.astimezone(timezone(obj.location.timezone))} ({obj.location.timezone})'
        else:
            return str(obj.start.astimezone(get_current_timezone()).tzinfo)

    timezone.short_description = _('Timezone')


@admin.register(DateActivity)
class DateActivityAdmin(TimeBasedAdmin):
    base_model = DateActivity
    form = TimeBasedActivityAdminForm
    inlines = (DateActivitySlotInline, DateParticipantAdminInline) + TimeBasedAdmin.inlines
    readonly_fields = TimeBasedAdmin.readonly_fields + ['team_activity']
    save_as = True

    list_filter = TimeBasedAdmin.list_filter + [
        ('expertise', SortedRelatedFieldListFilter),
    ]

    list_display = TimeBasedAdmin.list_display + [
        'start',
        'duration',
        'participant_count',
    ]

    def start(self, obj):
        first_slot = obj.slots.order_by('start').first()
        if first_slot:
            return first_slot.start

    def duration(self, obj):
        return obj.slots.count()

    duration.short_description = _('Slots')

    export_as_csv_fields = TimeBasedAdmin.export_to_csv_fields
    actions = [export_as_csv_action(fields=export_as_csv_fields)]


class DeadlineParticipantAdminInline(BaseContributorInline):
    model = DeadlineParticipant
    verbose_name = _("Participant")
    verbose_name_plural = _("Participants")


class ScheduleParticipantAdminInline(BaseContributorInline):
    model = ScheduleParticipant


class PeriodicParticipantAdminInline(BaseContributorInline):
    verbose_name = _("Participation")
    verbose_name_plural = _("Participation")
    model = PeriodicParticipant


class BaseRegistrationAdminInline(TabularInlinePaginated):
    verbose_name = _("Participant")
    verbose_name_plural = _("Participants")

    readonly_fields = ('status_label', 'edit')
    fields = ('edit', 'send_messages', 'user', 'status_label',)
    raw_id_fields = ('user',)

    def edit(self, obj):
        if not obj.user and obj.activity.has_deleted_data:
            return format_html(f'<i>{_("Anonymous")}</i>')
        if not obj.id:
            return '-'
        return format_html(
            '<a href="{}">{}</a>',
            reverse(
                'admin:time_based_{}_change'.format(obj.__class__.__name__.lower()),
                args=(obj.id,)),
            _('Edit')
        )

    def has_change_permission(self, request, obj=None):
        return False

    def status_label(self, obj):
        return obj.states.current_state.name

    status_label.short_description = _('Status')


class DeadlineRegistrationAdminInline(BaseRegistrationAdminInline):
    model = DeadlineRegistration


class ScheduleRegistrationAdminInline(BaseRegistrationAdminInline):
    model = ScheduleRegistration


class PeriodicRegistrationAdminInline(BaseRegistrationAdminInline):
    model = PeriodicRegistration


@admin.register(DeadlineActivity)
class DeadlineActivityAdmin(TimeBasedAdmin):
    base_model = DeadlineActivity

    inlines = (DeadlineParticipantAdminInline,) + TimeBasedAdmin.inlines
    raw_id_fields = TimeBasedAdmin.raw_id_fields + ['location']
    readonly_fields = TimeBasedAdmin.readonly_fields
    form = TimeBasedActivityAdminForm
    list_filter = TimeBasedAdmin.list_filter + [
        ('expertise', SortedRelatedFieldListFilter)
    ]

    list_display = TimeBasedAdmin.list_display + [
        'start', 'end_date', 'duration_string', 'participant_count'
    ]

    registration_fields = ("capacity",) + TimeBasedAdmin.registration_fields

    date_fields = [
        'duration',
        'start',
        'deadline',
        'is_online',
        'location',
        'location_hint',
        'online_meeting_url',
    ]

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        fieldsets.insert(2, (_("Date & time"), {"fields": self.date_fields}))
        return fieldsets

    export_as_csv_fields = TimeBasedAdmin.export_to_csv_fields + (
        ('deadline', 'Deadline'),
        ('duration', 'TimeContribution'),
    )
    actions = [export_as_csv_action(fields=export_as_csv_fields)]

    def end_date(self, obj):
        if not obj.deadline:
            return _('indefinitely')
        return obj.deadline

    def duration_string(self, obj):
        duration = get_human_readable_duration(str(obj.duration)).lower()
        return duration

    duration_string.short_description = _('Duration')


@admin.register(ScheduleActivity)
class ScheduleActivityAdmin(TimeBasedAdmin):
    base_model = ScheduleActivity

    inlines = (ScheduleParticipantAdminInline,) + TimeBasedAdmin.inlines
    raw_id_fields = TimeBasedAdmin.raw_id_fields + ['location']
    readonly_fields = TimeBasedAdmin.readonly_fields
    form = TimeBasedActivityAdminForm
    list_filter = TimeBasedAdmin.list_filter + [
        ('expertise', SortedRelatedFieldListFilter)
    ]

    list_display = TimeBasedAdmin.list_display + [
        "start",
        "end_date",
        "participant_count",
    ]

    date_fields = [
        'start',
        'deadline',
        'is_online',
        'location',
        'location_hint',
        'online_meeting_url',
    ]

    registration_fields = ("capacity",) + TimeBasedAdmin.registration_fields

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        fieldsets.insert(1, (
            _('Date & time'), {'fields': self.date_fields}
        ))
        return fieldsets

    export_as_csv_fields = TimeBasedAdmin.export_to_csv_fields + (
        ('deadline', 'Deadline'),
        ('duration', 'TimeContribution'),
    )
    actions = [export_as_csv_action(fields=export_as_csv_fields)]

    def end_date(self, obj):
        if not obj.deadline:
            return _('indefinitely')
        return obj.deadline

    def duration_string(self, obj):
        duration = get_human_readable_duration(str(obj.duration)).lower()
        return duration

    duration_string.short_description = _('Duration')

    def participant_count(self, obj):
        return obj.accepted_participants.count()

    participant_count.short_description = _("Participants")


@admin.register(PeriodicSlot)
class PeriodicSlotAdmin(StateMachineAdmin):
    list_display = ("start", "duration", "activity", "participant_count")
    inlines = (PeriodicParticipantAdminInline,)

    readonly_fields = ("activity", "status")
    fields = readonly_fields + ("start", "end", "duration")

    registration_fields = ("capacity",) + TimeBasedAdmin.registration_fields

    def participant_count(self, obj):
        return obj.accepted_participants.count()

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if request.user.is_superuser:
            fieldsets += ((_("Super admin"), {"fields": ("force_status", "states")}),)
        return fieldsets


@admin.register(ScheduleSlot)
class ScheduleSlotAdmin(StateMachineAdmin):
    list_display = ("start", "duration", "activity", "participant_count")
    raw_id_fields = ('activity',)
    readonly_fields = ("status",)
    fields = readonly_fields + ("activity", "start", "duration")

    def participant_count(self, obj):
        return obj.accepted_participants.count()

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if request.user.is_superuser:
            fieldsets += ((_("Super admin"), {"fields": ("force_status", "states")}),)
        return fieldsets


class PeriodicSlotAdminInline(TabularInlinePaginated):
    model = PeriodicSlot
    verbose_name = _("Slot")
    verbose_name_plural = _("Slots")
    readonly_fields = ("edit", "start", "end", "duration", "participant_count", "status_label")
    fields = readonly_fields

    def participant_count(self, obj):
        return obj.accepted_participants.count()

    participant_count.short_description = _('Participants')

    def current_status(self, obj):
        return obj.states.current_state.name

    current_status.short_description = _("Status")

    def has_add_permission(self, request, obj):
        return False

    def edit(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse(
                "admin:time_based_{}_change".format(obj.__class__.__name__.lower()),
                args=(obj.id,),
            ),
            _("Edit"),
        )

    def status_label(self, obj):
        return obj.states.current_state.name


@admin.register(PeriodicActivity)
class PeriodicActivityAdmin(TimeBasedAdmin):
    base_model = PeriodicActivity

    inlines = (PeriodicRegistrationAdminInline, PeriodicSlotAdminInline) + TimeBasedAdmin.inlines
    raw_id_fields = TimeBasedAdmin.raw_id_fields + ['location']
    readonly_fields = TimeBasedAdmin.readonly_fields
    form = TimeBasedActivityAdminForm
    list_filter = TimeBasedAdmin.list_filter + [
        ('expertise', SortedRelatedFieldListFilter)
    ]

    list_display = TimeBasedAdmin.list_display + [
        'start', 'end_date', 'duration_string', 'participant_count'
    ]

    date_fields = [
        'period',
        'duration',
        'start',
        'deadline',
        'is_online',
        'location',
        'location_hint',
        'online_meeting_url',
    ]

    registration_fields = ("capacity",) + TimeBasedAdmin.registration_fields

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        fieldsets.insert(1, (
            _('Date & time'), {'fields': self.date_fields}
        ))
        return fieldsets

    export_as_csv_fields = TimeBasedAdmin.export_to_csv_fields + (
        ('deadline', 'Deadline'),
        ('duration', 'duration'),
        ('period', 'period'),
    )
    actions = [export_as_csv_action(fields=export_as_csv_fields)]

    def end_date(self, obj):
        if not obj.deadline:
            return _('indefinitely')
        return obj.deadline

    def duration_string(self, obj):
        duration = get_human_readable_duration(str(obj.duration)).lower()
        return duration

    duration_string.short_description = _('Duration')


class SlotParticipantInline(admin.TabularInline):
    model = SlotParticipant
    readonly_fields = ['participant_link', 'smart_status', 'participant_status']
    fields = readonly_fields

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    verbose_name = _('Participant')
    verbose_name_plural = _('Participants')

    def participant_link(self, obj):
        url = reverse('admin:time_based_dateparticipant_change', args=(obj.participant.id,))
        return format_html('<a href="{}">{}</a>', url, obj.participant)

    def participant_status(self, obj):
        return obj.participant.status

    def smart_status(self, obj):
        return obj.status

    smart_status.short_description = _('Registered')


class SlotAdmin(StateMachineAdmin):
    raw_id_fields = ['activity', 'location']

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

    def activity_link(self, obj):
        url = reverse(
            'admin:time_based_{}_change'.format(obj.activity._meta.model_name),
            args=(obj.activity.id,)
        )
        return format_html('<a href="{}">{}</a>', url, obj.activity)

    activity_link.short_description = _('Activity')

    def get_form(self, request, obj=None, **kwargs):
        if obj and not obj.is_online and obj.location:
            local_start = obj.start.astimezone(timezone(obj.location.timezone))
            platform_start = obj.start.astimezone(get_current_timezone())
            offset = local_start.utcoffset() - platform_start.utcoffset()

            if offset.total_seconds() != 0:
                timezone_text = _(
                    'Local time in "{location}" is {local_time}. '
                    'This is {offset} hours {relation} compared to the '
                    'standard platform timezone ({current_timezone}).'
                ).format(
                    location=obj.location,
                    local_time=defaultfilters.time(local_start),
                    offset=abs(offset.total_seconds() / 3600.0),
                    relation=_('later') if offset.total_seconds() > 0 else _('earlier'),
                    current_timezone=get_current_timezone()
                )

                help_texts = {'start': timezone_text}
                kwargs.update({'help_texts': help_texts})

        return super(SlotAdmin, self).get_form(request, obj, **kwargs)

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
    detail_fields = [
        'activity',
        'is_online',
        'location',
        'location_hint',
        'online_meeting_url'
    ]
    status_fields = [
        'status',
        'states',
        'created',
        'updated'
    ]

    def get_status_fields(self, request, obj):
        fields = self.status_fields
        if obj and obj.status in ('draft',):
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


class SlotTimeFilter(SimpleListFilter):
    title = _('Date')
    parameter_name = 'date'

    def lookups(self, request, model_admin):
        return [
            ('all', _('All')),
            ('upcoming', _('Upcoming')),
            ('passed', _('Passed')),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'all':
            return queryset
        elif self.value() == 'upcoming':
            return queryset.filter(
                start__date__gte=now().date()
            )
        elif self.value() == 'passed':
            return queryset.filter(
                start__date__lte=now().date()
            )
        else:
            return queryset


class RequiredSlotFilter(SimpleListFilter):
    title = _('Slot required')
    parameter_name = 'required'

    def lookups(self, request, model_admin):
        return [
            ('all', _('All')),
            ('required', _('Required')),
            ('optional', _('Optional')),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'all':
            return queryset
        elif self.value() == 'required':
            return queryset.filter(
                activity__slot_selection='all'
            )
        elif self.value() == 'optional':
            return queryset.filter(
                activity__slot_selection='free'
            )
        else:
            return queryset


class SlotDuplicateForm(forms.Form):
    INTERVAL_CHOICES = (
        ('day', _('day')),
        ('week', _('week')),
        ('month', _('xth weekday of the month')),
        ('monthday', _('day x of the month')),
    )

    interval = forms.ChoiceField(
        label=_('Repeat'),
        choices=INTERVAL_CHOICES,
    )

    end = forms.DateField(
        label=_('End date'),
        help_text=_('Select a date until which the series runs. If you plan '
                    'further than 6 months in the future, '
                    'the loading time can be quite long.'),
        widget=widgets.AdminDateWidget()
    )

    title = _('Duplicate slot')

    def __init__(self, slot, data=None, *args, **kwargs):
        start = slot.start
        if slot.location:
            start = start.astimezone(timezone(slot.location.timezone))
        if data:
            super(SlotDuplicateForm, self).__init__(data)
        else:
            super(SlotDuplicateForm, self).__init__()
        interval_day = _('Every day')
        interval_week = _('Each week on {weekday}').format(
            weekday=start.strftime('%A')
        )
        interval_month = _('Monthly every {nth} {weekday}').format(
            nth=ordinalize(nth_weekday(start)),
            weekday=start.strftime('%A')
        )
        interval_monthday = _('Monthly every {monthday}').format(
            monthday=ordinalize(slot.start.strftime('%-d'))
        )
        interval_choices = (
            ('day', interval_day),
            ('week', interval_week),
            ('monthday', interval_monthday),
            ('month', interval_month),
        )
        self.fields['interval'].choices = interval_choices
        self.fields['interval'].help_text = _(
            'We selected these choices because this slot takes place {start}'
        ).format(start=start.strftime('%A %-d %B %Y %H:%M %Z'))


class SlotBulkAddForm(forms.Form):
    emails = forms.CharField(
        label=_('Emails'),
        help_text=_('Enter one email address per line'),
        widget=forms.Textarea
    )

    title = _('Bulk add participants')

    def __init__(self, slot, data=None, *args, **kwargs):
        if data:
            super(SlotBulkAddForm, self).__init__(data)
        else:
            super(SlotBulkAddForm, self).__init__()
        self.fields['emails'].help_text = _(
            'Enter the email addresses of the participants you want to add to this slot.'
        )


@admin.register(DateActivitySlot)
class DateSlotAdmin(SlotAdmin):
    model = DateActivitySlot
    inlines = [SlotParticipantInline, MessageAdminInline]

    def lookup_allowed(self, lookup, value):
        if lookup == 'activity__slot_selection__exact':
            return True
        return super(DateSlotAdmin, self).lookup_allowed(lookup, value)

    date_hierarchy = 'start'
    list_display = [
        '__str__', 'start', 'activity_link', 'attendee_limit', 'participants', 'duration_string', 'required',
    ]
    list_filter = [
        'status',
        SlotTimeFilter,
        RequiredSlotFilter,
    ]

    def attendee_limit(self, obj):
        return obj.capacity or obj.activity.capacity

    def participants(self, obj):
        return obj.accepted_participants.count()

    participants.short_description = _('Accepted participants')

    def required(self, obj):
        if obj.activity.slot_selection == 'free':
            return _('Optional')
        return _('Required')

    required.short_description = _('Required')

    detail_fields = SlotAdmin.detail_fields + [
        'title',
        'capacity',
        'start',
        'duration',
    ]

    def get_urls(self):
        urls = super(DateSlotAdmin, self).get_urls()

        extra_urls = [
            url(r'^(?P<pk>\d+)/duplicate/$',
                self.admin_site.admin_view(self.duplicate_slot),
                name='time_based_dateactivityslot_duplicate'
                ),
            url(r'^(?P<pk>\d+)/bulk_add/$',
                self.admin_site.admin_view(self.bulk_add_participants),
                name='time_based_dateactivityslot_bulk_add'
                ),
        ]
        return extra_urls + urls

    def duplicate_slot(self, request, pk, *args, **kwargs):
        slot = DateActivitySlot.objects.get(pk=pk)
        if request.method == "POST":
            form = SlotDuplicateForm(data=request.POST, slot=slot)
            if form.is_valid():
                data = form.cleaned_data
                duplicate_slot(slot, data['interval'], data['end'])
                slot_overview = reverse('admin:time_based_dateactivity_change', args=(slot.activity.pk,))
                return HttpResponseRedirect(slot_overview + '#/tab/inline_0/')

        if slot.location:
            start = slot.start.astimezone(timezone(slot.location.timezone))
        else:
            start = slot.start

        context = {
            'opts': self.model._meta,
            'slot': slot,
            'time': start.strftime('%H:%M %Z'),
            'form': SlotDuplicateForm(slot=slot)
        }
        return TemplateResponse(
            request, 'admin/time_based/duplicate_slot.html', context
        )

    def bulk_add_participants(self, request, pk, *args, **kwargs):
        slot = DateActivitySlot.objects.get(pk=pk)
        slot_overview = reverse('admin:time_based_dateactivityslot_change', args=(slot.pk,))

        if not request.user.is_superuser:
            return HttpResponseRedirect(slot_overview + '#/tab/inline_0/')

        if request.method == "POST":
            form = SlotBulkAddForm(data=request.POST, slot=slot)
            if form.is_valid():
                data = form.cleaned_data
                emails = data['emails'].split('\n')
                result = bulk_add_participants(slot, emails)
                messages.add_message(request, messages.INFO, '{} participants were added'.format(result))
                return HttpResponseRedirect(slot_overview + '#/tab/inline_0/')

        context = {
            'opts': self.model._meta,
            'slot': slot,
            'form': SlotBulkAddForm(slot=slot)
        }
        return TemplateResponse(
            request, 'admin/time_based/bulk_add.html', context
        )


class TimeContributionInlineAdmin(admin.TabularInline):
    model = TimeContribution
    extra = 0
    readonly_fields = ('edit', 'contribution_type', 'status', 'start',)
    fields = readonly_fields + ('value',)

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
            _('Edit')
        )


@admin.register(TimeContribution)
class TimeContributionAdmin(ContributionChildAdmin):
    raw_id_fields = ContributionChildAdmin.raw_id_fields + ('slot_participant',)
    fields = ['contributor', 'slot_participant', 'created', 'start', 'end', 'value', 'status', 'states']


class SlotWidget(TextInput):
    template_name = 'admin/widgets/slot_widget.html'


class ParticipantSlotForm(ModelForm):
    checked = BooleanField(label=_('Participating'), required=False)

    def __init__(self, *args, **kwargs):
        super(ParticipantSlotForm, self).__init__(*args, **kwargs)
        slot = ''
        initial = kwargs.get('initial', None)
        if initial:
            slot = initial['slot']
        instance = kwargs.get('instance', None)
        if instance:
            slot = instance.slot
            sm = SlotParticipantStateMachine
            self.fields['checked'].initial = instance.status in [sm.registered.value, sm.succeeded.value]
        self.fields['slot'].label = _('Slot')
        self.fields['slot'].widget = SlotWidget(attrs={'slot': slot})

    class Meta:
        model = SlotParticipant
        fields = ['slot', 'checked']

    def save(self, commit=True):
        self.is_valid()
        if not self.cleaned_data['checked']:
            self.instance = None
        else:
            return super().save(commit)


class ParticipantSlotFormSet(BaseInlineFormSet):

    def __init__(self, *args, **kwargs):
        if 'data' not in kwargs:
            instance = kwargs['instance']
            new = []
            for slot in instance.activity.slots.exclude(slot_participants__participant=instance).all():
                new.append({
                    'slot': slot,
                    'checked': False
                })

            kwargs.update({'initial': new})
        super(ParticipantSlotFormSet, self).__init__(*args, **kwargs)

    @property
    def extra_forms(self):
        """Ignore extra forms that aren't checked"""
        extra_forms = super().extra_forms
        if self.data:
            extra_forms = [form for form in extra_forms if form.cleaned_data['checked']]
        return extra_forms

    def save_existing(self, form, instance, commit=True):
        """Transition the slot participant as needed before saving"""
        sm = SlotParticipantStateMachine
        checked = form.cleaned_data['checked']
        form.instance.execute_triggers(send_messages=False)
        if form.instance.status in [sm.registered.value, sm.succeeded.value] and not checked:
            form.instance.states.remove(save=commit)
        elif checked and form.instance.status in [sm.removed.value, sm.withdrawn.value, sm.cancelled.value]:
            form.instance.states.accept(save=commit)
        return form.save(commit=commit)


class ParticipantSlotInline(admin.TabularInline):
    parent_object = None
    model = SlotParticipant
    formset = ParticipantSlotFormSet
    form = ParticipantSlotForm

    def get_extra(self, request, obj=None, **kwargs):
        ids = [sp.slot_id for sp in self.parent_object.slot_participants.all()]
        return self.parent_object.activity.slots.exclude(id__in=ids).count()

    readonly_fields = ['status']
    fields = ['slot', 'checked', 'status']

    def has_delete_permission(self, request, obj=None):
        return False

    verbose_name = _('slot')
    verbose_name_plural = _('slots')


@admin.register(DateParticipant)
class DateParticipantAdmin(ContributorChildAdmin):
    formfield_overrides = {
        PrivateDocumentModelChoiceField: {'widget': DocumentWidget}
    }

    def get_inline_instances(self, request, obj=None):
        inlines = super().get_inline_instances(request, obj)
        for inline in inlines:
            inline.parent_object = obj
        return inlines

    inlines = ContributorChildAdmin.inlines + [
        ParticipantSlotInline,
        TimeContributionInlineAdmin
    ]
    fields = ContributorChildAdmin.fields + ['motivation', 'document']
    list_display = ['__str__', 'email', 'activity_link', 'status']

    def email(self, obj):
        return obj.user.email

    export_to_csv_fields = (
        ('id', 'ID'),
        ('user__full_name', 'Name'),
        ('user__email', 'Email'),
        ('status', 'Status'),
        ('created', 'Created'),
    )

    def get_actions(self, request):
        self.actions = (export_as_csv_action(fields=self.export_to_csv_fields),)
        return super(DateParticipantAdmin, self).get_actions(request)


@admin.register(DeadlineParticipant)
class DeadlineParticipantAdmin(ContributorChildAdmin):

    def get_inline_instances(self, request, obj=None):
        inlines = super().get_inline_instances(request, obj)
        for inline in inlines:
            inline.parent_object = obj
        return inlines

    inlines = ContributorChildAdmin.inlines + [
        TimeContributionInlineAdmin
    ]
    fields = ContributorChildAdmin.fields + ['registration_info']
    pending_fields = ['activity', 'user', 'registration_info', 'created', 'updated']

    def get_fields(self, request, obj=None):
        if obj and obj.registration and obj.registration.status == 'new':
            return self.pending_fields
        return self.fields

    readonly_fields = ContributorChildAdmin.readonly_fields + [
        'registration_info'
    ]

    def registration_info(self, obj):
        url = reverse("admin:{}_{}_change".format(
            obj.registration._meta.app_label,
            obj.registration._meta.model_name),
            args=(obj.registration.id,)
        )
        status = obj.registration.states.current_state.name
        if obj.registration.status == 'new':
            template = loader.get_template(
                'admin/time_based/registration_info.html'
            )
            return template.render({'status': status, 'url': url})
        else:
            title = _('Change review')
            return format_html(
                'Current status <b>{status}</b>. <a href="{url}">{title}</a>',
                url=url, status=status, title=title
            )

    registration_info.short_description = _('Registration')

    list_display = ['__str__', 'activity_link', 'status']


@admin.register(PeriodicParticipant)
class PeriodicParticipantAdmin(ContributorChildAdmin):
    raw_id_fields = ContributorChildAdmin.raw_id_fields + ("slot",)

    def get_inline_instances(self, request, obj=None):
        inlines = super().get_inline_instances(request, obj)
        for inline in inlines:
            inline.parent_object = obj
        return inlines

    inlines = ContributorChildAdmin.inlines + [
        TimeContributionInlineAdmin
    ]

    fields = ContributorChildAdmin.fields + ["registration_info", "slot_info", "slot"]
    pending_fields = ["activity", "user", "registration_info", "created", "updated"]

    def get_fields(self, request, obj=None):
        if obj and obj.registration and obj.registration.status == 'new':
            return self.pending_fields
        return self.fields

    readonly_fields = ContributorChildAdmin.readonly_fields + [
        "registration_info",
        "slot_info",
    ]

    def registration_info(self, obj):
        url = reverse("admin:{}_{}_change".format(
            obj.registration._meta.app_label,
            obj.registration._meta.model_name),
            args=(obj.registration.id,)
        )
        status = obj.registration.states.current_state.name
        if obj.registration.status == 'new':
            template = loader.get_template(
                'admin/time_based/registration_info.html'
            )
            return template.render({'status': status, 'url': url})
        else:
            title = _('Change review')
            return format_html(
                'Current status <b>{status}</b>. <a href="{url}">{title}</a>',
                url=url, status=status, title=title
            )

    def slot_info(self, obj):
        if not obj.slot:
            return "-"
        return format_html("{} to {}", obj.slot.start.date(), obj.slot.end.date())

    registration_info.short_description = _("Registration")

    list_display = ["__str__", "activity_link", "status"]


@admin.register(ScheduleParticipant)
class ScheduleParticipantAdmin(ContributorChildAdmin):

    raw_id_fields = ContributorChildAdmin.raw_id_fields + ("slot",)

    def get_inline_instances(self, request, obj=None):
        inlines = super().get_inline_instances(request, obj)
        for inline in inlines:
            inline.parent_object = obj
        return inlines

    inlines = ContributorChildAdmin.inlines + [TimeContributionInlineAdmin]

    fields = ContributorChildAdmin.fields + ["registration_info", "slot_info", "slot"]
    pending_fields = ["activity", "user", "registration_info", "created", "updated"]

    def get_fields(self, request, obj=None):
        if obj and obj.registration and obj.registration.status == "new":
            return self.pending_fields
        return self.fields

    readonly_fields = ContributorChildAdmin.readonly_fields + [
        "registration_info",
        "slot_info",
    ]

    def registration_info(self, obj):
        url = reverse(
            "admin:{}_{}_change".format(
                obj.registration._meta.app_label, obj.registration._meta.model_name
            ),
            args=(obj.registration.id,),
        )
        status = obj.registration.states.current_state.name
        if obj.registration.status == "new":
            template = loader.get_template("admin/time_based/registration_info.html")
            return template.render({"status": status, "url": url})
        else:
            title = _("Change review")
            return format_html(
                'Current status <b>{status}</b>. <a href="{url}">{title}</a>',
                url=url,
                status=status,
                title=title,
            )

    def slot_info(self, obj):
        if not obj.slot:
            return "-"
        return format_html("{} to {}", obj.slot.start.date(), obj.slot.end.date())

    registration_info.short_description = _('Registration')

    list_display = ['__str__', 'activity_link', 'status']


@admin.register(Registration)
class RegistrationAdmin(PolymorphicParentModelAdmin, StateMachineAdmin):
    base_model = Registration
    child_models = (
        PeriodicRegistration,
        DeadlineRegistration
    )
    list_display = ['created', 'user', 'type', 'activity', 'state_name']
    list_filter = (PolymorphicChildModelFilter, StateMachineFilter,)
    date_hierarchy = 'created'

    ordering = ('-created',)

    def type(self, obj):
        return obj.get_real_instance_class()._meta.verbose_name


class RegistrationChildAdmin(PolymorphicInlineSupportMixin, PolymorphicChildModelAdmin, StateMachineAdmin):
    base_model = Registration
    readonly_fields = [
        "created",
    ]
    raw_id_fields = ["user", "activity", "document"]
    fields = ["user", "activity", "answer", "document", "status", "states"]
    list_display = ["__str__", "activity", "user", "status"]

    formfield_overrides = {PrivateDocumentModelChoiceField: {"widget": DocumentWidget}}

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if request.user.is_superuser:
            fieldsets += [
                (_("Super admin"), {"fields": ("force_status",)}),
            ]
        return fieldsets


@admin.register(DeadlineRegistration)
class DeadlineRegistrationAdmin(RegistrationChildAdmin):
    inlines = [DeadlineParticipantAdminInline]


@admin.register(ScheduleRegistration)
class ScheduleRegistrationAdmin(RegistrationChildAdmin):
    inlines = [ScheduleParticipantAdminInline]


@admin.register(PeriodicRegistration)
class PeriodicRegistrationAdmin(RegistrationChildAdmin):
    inlines = [PeriodicParticipantAdminInline]


@admin.register(SlotParticipant)
class SlotParticipantAdmin(StateMachineAdmin):
    raw_id_fields = ['participant', 'slot']
    list_display = ['participant', 'slot']

    inlines = [TimeContributionInlineAdmin]

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

    detail_fields = ['participant', 'slot']
    status_fields = ['status', 'states']

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (_('Detail'), {'fields': self.detail_fields}),
            (_('Status'), {'fields': self.status_fields}),
        )
        if request.user.is_superuser:
            fieldsets += (
                (_('Super admin'), {'fields': (
                    'force_status',
                )}),
            )
        return fieldsets


@admin.register(Skill)
class SkillAdmin(TranslatableAdminOrderingMixin, TranslatableAdmin):
    list_display = ('name', 'member_link')
    readonly_fields = ('member_link',)
    fields = readonly_fields + ('name', 'disabled', 'description', 'expertise')

    def get_actions(self, request):
        actions = super(SkillAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def member_link(self, obj):
        url = "{}?skills__id__exact={}".format(reverse('admin:members_member_changelist'), obj.id)
        return format_html(
            "<a href='{}'>{} {}</a>",
            url, obj.member_set.count(), _('users')
        )

    member_link.short_description = _('Users with this skill')
