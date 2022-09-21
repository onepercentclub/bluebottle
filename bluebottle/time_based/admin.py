from django import forms
from django.conf.urls import url
from django.contrib import admin
from django.contrib.admin import SimpleListFilter, widgets
from django.db import models
from django.db.models import Sum
from django.forms import Textarea, BaseInlineFormSet, ModelForm, BooleanField, TextInput
from django.http import HttpResponseRedirect
from django.template import loader, defaultfilters
from django.template.response import TemplateResponse
from django.urls import reverse, resolve
from django.utils.html import format_html
from django.utils.timezone import get_current_timezone, now
from django.utils.translation import gettext_lazy as _
from django_admin_inline_paginator.admin import TabularInlinePaginated
from django_summernote.widgets import SummernoteWidget
from inflection import ordinalize
from parler.admin import SortedRelatedFieldListFilter, TranslatableAdmin
from parler.utils.views import get_language_parameter
from pytz import timezone

from bluebottle.activities.admin import (
    ActivityChildAdmin, ContributorChildAdmin, ContributionChildAdmin, ActivityForm, TeamInline
)
from bluebottle.activities.models import Team
from bluebottle.fsm.admin import StateMachineFilter, StateMachineAdmin
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.notifications.admin import MessageAdminInline
from bluebottle.time_based.models import (
    DateActivity, PeriodActivity, DateParticipant, PeriodParticipant, Participant, TimeContribution, DateActivitySlot,
    SlotParticipant, Skill, PeriodActivitySlot, TeamSlot
)
from bluebottle.time_based.states import SlotParticipantStateMachine
from bluebottle.time_based.utils import nth_weekday, duplicate_slot
from bluebottle.utils.admin import export_as_csv_action
from bluebottle.utils.widgets import TimeDurationWidget, get_human_readable_duration


class BaseParticipantAdminInline(TabularInlinePaginated):
    model = Participant
    per_page = 20
    readonly_fields = ('contributor_date', 'motivation', 'document', 'edit',
                       'created', 'transition_date', 'status')
    raw_id_fields = ('user', 'document')
    extra = 0
    ordering = ['-created']

    def get_template(self):
        pass

    def can_edit(self, obj):
        return obj and obj.id and obj.status in ['open', 'succeeded', 'full', 'submitted']

    def has_delete_permission(self, request, obj=None):
        return self.can_edit(obj)

    def has_add_permission(self, request, obj=None):
        activity = self.get_parent_object_from_request(request)
        return self.can_edit(activity)

    def get_parent_object_from_request(self, request):
        """
        Returns the parent object from the request or None.

        Note that this only works for Inlines, because the `parent_model`
        is not available in the regular admin.ModelAdmin as an attribute.
        """
        resolved = resolve(request.path_info)
        if 'object_id' in resolved.kwargs:
            return self.parent_model.objects.get(pk=resolved.kwargs['object_id'])
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


class DateParticipantAdminInline(BaseParticipantAdminInline):
    model = DateParticipant
    verbose_name = _("Participant")
    verbose_name_plural = _("Participants")
    readonly_fields = BaseParticipantAdminInline.readonly_fields
    fields = ('edit', 'user', 'status')


class PeriodParticipantForm(ModelForm):

    activity = None

    class Meta:
        model = PeriodParticipant
        exclude = []

    def __init__(self, *args, **kwargs):
        super(PeriodParticipantForm, self).__init__(*args, **kwargs)
        if self.activity and 'team' in self.fields:
            self.fields['team'].queryset = Team.objects.filter(activity=self.activity)

    def full_clean(self):
        data = super(PeriodParticipantForm, self).full_clean()
        if not self.instance.activity_id and self.instance.team_id:
            self.instance.activity = self.instance.team.activity
        return data


class PeriodParticipantAdminInline(BaseParticipantAdminInline):
    model = PeriodParticipant
    verbose_name = _("Participant")
    verbose_name_plural = _("Participants")
    raw_id_fields = BaseParticipantAdminInline.raw_id_fields
    fields = ('edit', 'user', 'status')
    form = PeriodParticipantForm

    def get_parent_object_from_request(self, request):
        """
        Returns the parent object from the request or None.
        """
        resolved = resolve(request.path_info)
        if resolved.kwargs:
            return self.parent_model.objects.get(pk=resolved.kwargs['object_id'])
        return None

    def get_formset(self, request, obj=None, **kwargs):
        # Set activity on form so we can filter teams for new participants too
        formset = super(PeriodParticipantAdminInline, self).get_formset(request, obj, **kwargs)
        parent = self.get_parent_object_from_request(request)
        if isinstance(parent, PeriodActivity):
            formset.form.activity = parent
        return formset

    def get_fields(self, request, obj=None):
        fields = super(PeriodParticipantAdminInline, self).get_fields(request, obj)
        if isinstance(obj, PeriodActivity):
            if obj and obj.team_activity == 'teams':
                fields += ('team',)
        return fields


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

    raw_id_fields = ActivityChildAdmin.raw_id_fields

    export_to_csv_fields = (
        ('title', 'Title'),
        ('description', 'Description'),
        ('status', 'Status'),
        ('created', 'Created'),
        ('initiative__title', 'Initiative'),
        ('registration_deadline', 'Registration Deadline'),
        ('owner__full_name', 'Owner'),
        ('owner__email', 'Email'),
        ('fallback_location', 'Office Location'),
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


class TimeBasedActivityAdminForm(ActivityForm):
    class Meta(object):
        model = PeriodActivity
        fields = '__all__'
        widgets = {
            'description': SummernoteWidget(attrs={'height': 400})
        }


class DateActivityASlotInline(TabularInlinePaginated):
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


class TeamSlotForm(ModelForm):

    class Meta:
        model = TeamSlot
        exclude = []

    def full_clean(self):
        data = super(TeamSlotForm, self).full_clean()
        if not self.instance.activity_id and self.instance.team_id:
            self.instance.activity = self.instance.team.activity
        return data


class TeamSlotInline(admin.StackedInline):
    model = TeamSlot

    form = TeamSlotForm
    verbose_name = _('Time slot')
    verbose_name_plural = _('Time slot')
    raw_id_fields = ('location', )

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
    readonly_fields = ['link', 'timezone', 'status']
    fields = [
        'start',
        'duration',
        'timezone',
        'location',
        'is_online',
        'status',
    ]

    def timezone(self, obj):
        if not obj.is_online and obj.location:
            return obj.location.timezone
        else:
            return str(obj.start.astimezone(get_current_timezone()).tzinfo)
    timezone.short_description = _('Timezone')


@admin.register(DateActivity)
class DateActivityAdmin(TimeBasedAdmin):
    base_model = DateActivity
    form = TimeBasedActivityAdminForm
    inlines = (TeamInline, DateActivityASlotInline, DateParticipantAdminInline,) + TimeBasedAdmin.inlines
    readonly_fields = TimeBasedAdmin.readonly_fields + ['team_activity']

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

    def participant_count(self, obj):
        return obj.accepted_participants.count()
    participant_count.short_description = _('Participants')

    detail_fields = ActivityChildAdmin.detail_fields + (
        'slot_selection',

        'preparation',
        'registration_deadline',

        'expertise',
        'capacity',
        'review',

    )

    export_as_csv_fields = TimeBasedAdmin.export_to_csv_fields
    actions = [export_as_csv_action(fields=export_as_csv_fields)]


@admin.register(PeriodActivity)
class PeriodActivityAdmin(TimeBasedAdmin):
    base_model = PeriodActivity

    inlines = (TeamInline, PeriodParticipantAdminInline,) + TimeBasedAdmin.inlines
    raw_id_fields = TimeBasedAdmin.raw_id_fields + ['location']
    form = TimeBasedActivityAdminForm
    list_filter = TimeBasedAdmin.list_filter + [
        ('expertise', SortedRelatedFieldListFilter)
    ]

    list_display = TimeBasedAdmin.list_display + [
        'start', 'end_date', 'duration_string', 'participant_count'
    ]

    def get_detail_fields(self, request, obj):
        fields = ActivityChildAdmin.detail_fields + (
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
        initiative_settings = InitiativePlatformSettings.load()
        if initiative_settings.team_activities:
            fields += ('team_activity',)
        return fields

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

    def duration_string(self, obj):
        duration = get_human_readable_duration(str(obj.duration)).lower()
        if obj.duration_period and obj.duration_period != 'overall':
            return _('{duration} per {time_unit}').format(
                duration=duration,
                time_unit=obj.duration_period[0:-1])
        return duration
    duration_string.short_description = _('Duration')

    def participant_count(self, obj):
        return obj.accepted_participants.count()
    participant_count.short_description = _('Participants')


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


@admin.register(DateActivitySlot)
class DateSlotAdmin(SlotAdmin):
    model = DateActivitySlot
    inlines = [SlotParticipantInline]

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


@admin.register(PeriodActivitySlot)
class PeriodSlotAdmin(SlotAdmin):
    model = PeriodActivitySlot

    date_hierarchy = 'start'
    list_display = [
        '__str__', 'start', 'activity_link',
    ]
    list_filter = [
        'status',
        SlotTimeFilter,
        RequiredSlotFilter,
    ]

    def participants(self, obj):
        return obj.accepted_participants.count()
    participants.short_description = _('Accepted participants')


@admin.register(TeamSlot)
class TeamSlotAdmin(SlotAdmin):
    model = TeamSlot
    raw_id_fields = SlotAdmin.raw_id_fields + ['team']
    date_hierarchy = 'start'
    list_display = [
        '__str__', 'start', 'activity_link',
    ]
    list_filter = [
        'status',
        SlotTimeFilter,
        RequiredSlotFilter,
    ]
    detail_fields = SlotAdmin.detail_fields + [
        'team',
    ]

    def participants(self, obj):
        return obj.accepted_participants.count()
    participants.short_description = _('Accepted participants')


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
            _('Edit duration')
        )


@admin.register(PeriodParticipant)
class PeriodParticipantAdmin(ContributorChildAdmin):
    inlines = ContributorChildAdmin.inlines + [TimeContributionInlineAdmin]
    readonly_fields = ContributorChildAdmin.readonly_fields + ['total']
    fields = ContributorChildAdmin.fields + ['total', 'motivation', 'current_period', 'document']
    raw_id_fields = ContributorChildAdmin.raw_id_fields + ('document', )
    list_display = ['__str__', 'activity_link', 'status']

    def total(self, obj):
        if not obj:
            return '-'
        return obj.contributions.aggregate(total=Sum('timecontribution__value'))['total']

    total.short_description = _('Total contributed')


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
    list_display = ['__str__', 'activity_link', 'status']


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
class SkillAdmin(TranslatableAdmin):
    list_display = ('name', 'member_link')
    readonly_fields = ('member_link',)
    fields = readonly_fields + ('name', 'disabled', 'description', 'expertise')

    def get_queryset(self, request):
        lang = get_language_parameter(request, self.query_language_key)
        return super().get_queryset(request).translated(lang).order_by('translations__name')

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
