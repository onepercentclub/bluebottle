from urllib.parse import urlencode

from django import forms
from django.urls import re_path
from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter, widgets, StackedInline
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
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
    ContributorChildAdmin, BaseContributorInline, BulkAddMixin,
)
from bluebottle.files.fields import PrivateDocumentModelChoiceField
from bluebottle.files.widgets import DocumentWidget
from bluebottle.fsm.admin import StateMachineAdmin, StateMachineFilter, StateMachineAdminMixin
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.notifications.admin import MessageAdminInline
from bluebottle.offices.admin import RegionManagerAdminMixin
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
    BaseScheduleSlot,
    Skill,
    SlotParticipant,
    TimeContribution, Registration, PeriodicSlot, ScheduleActivity, ScheduleParticipant, ScheduleRegistration,
    TeamScheduleRegistration, TeamScheduleParticipant, TeamScheduleSlot, Team, TeamMember, ActivitySlot, )
from bluebottle.time_based.states import SlotParticipantStateMachine
from bluebottle.time_based.utils import duplicate_slot, nth_weekday
from bluebottle.updates.admin import UpdateInline
from bluebottle.utils.admin import TranslatableAdminOrderingMixin, export_as_csv_action, admin_info_box
from bluebottle.utils.widgets import TimeDurationWidget, get_human_readable_duration


class DateParticipantAdminInline(BaseContributorInline):
    model = DateParticipant
    verbose_name = _("Participant")
    verbose_name_plural = _("Participants")


class TimeBasedAdmin(ActivityChildAdmin):
    inlines = (UpdateInline, )
    skip_on_duplicate = ActivityChildAdmin.skip_on_duplicate + [
        Registration,
    ]

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
        'preparation',
        'registration_deadline',
        'registration_flow',
        'registration_question',
        'review_title',
        'review_description',
        'review_document_enabled',
        'registration_link',
        'review_link',
    )

    readonly_fields = ActivityChildAdmin.readonly_fields + ['registration_link', 'registration_question']

    def registration_link(self, obj):
        return admin_info_box(
            _("Answer this question if you selected 'Direct the participants to a questionnaire'")
        )

    def registration_question(self, obj):
        return admin_info_box(
            _("Answer these questions if you selected 'Ask a single question on the platform'")
        )

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
    per_page = 10
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
    readonly_fields = ['link', 'timezone', 'status_label']
    fields = [
        'link',
        'start',
        'timezone',
        'duration',
        'status_label'
    ]

    extra = 0

    def link(self, obj):
        url = reverse('admin:time_based_dateactivityslot_change', args=(obj.id,))
        return format_html('<a href="{}">{}</a>', url, obj)

    def timezone(self, obj):
        if not obj.is_online and obj.location:
            return f'{obj.location.timezone}'
        else:
            return str(obj.start.astimezone(get_current_timezone()).tzinfo)
    timezone.short_description = _('Timezone')

    def status_label(self, obj):
        return obj.states.current_state.name
    status_label.short_description = _('Status')


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
    verbose_name = _("Participant")
    verbose_name_plural = _("Participants")

    fields = ['edit', 'slot_date', 'user', 'status_label']
    readonly_fields = BaseContributorInline.readonly_fields + ['slot_date']

    def slot_date(self, obj):
        if obj.slot:
            return obj.slot.start.strftime('%Y-%m-%d %H:%M')
        else:
            return format_html('<i>{}</i>', _('unscheduled'))


class TeamScheduleParticipantAdminInline(BaseContributorInline):
    model = TeamScheduleParticipant
    verbose_name = _("Team participants")
    verbose_name_plural = _("Team participants")

    readonly_fields = BaseContributorInline.readonly_fields + ['team_name']
    fields = BaseContributorInline.fields + ['team_name']

    def team_name(self, obj):
        return obj.team_member.team


class TeamScheduleRegistrationAdminInline(BaseContributorInline):
    model = TeamScheduleRegistration
    verbose_name = _("Team registration")
    verbose_name_plural = _("Team registrations")


@admin.register(TeamMember)
class TeamMemberAdmin(RegionManagerAdminMixin, StateMachineAdmin):
    model = TeamMember
    inlines = [TeamScheduleParticipantAdminInline]
    list_display = ('user', 'status', 'created',)
    readonly_fields = ('team', 'created')
    fields = ('team', 'user', 'status', 'states', 'created')
    raw_id_fields = ('user', 'team')

    superadmin_fields = ['force_status']

    def get_fieldsets(self, request, obj=None):
        fields = self.get_fields(request, obj)
        fieldsets = (
            (_('Details'), {'fields': fields}),
        )
        if request.user.is_superuser:
            fieldsets += (
                (_('Super admin'), {'fields': self.superadmin_fields}),
            )
        return fieldsets


class TeamMemberAdminInline(TabularInlinePaginated):
    model = TeamMember
    fields = ('link', 'status_label', 'user',)
    raw_id_fields = ('user',)

    def has_change_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj):
        return True

    can_delete = True

    readonly_fields = ('link', 'status_label')

    def status_label(self, obj):
        return obj.states.current_state.name

    status_label.short_description = _('Status')

    def link(self, obj):
        url = reverse('admin:time_based_teammember_change', args=(obj.id,))
        return format_html('<a href="{}">{}</a>', url, obj)

    link.short_description = _('Edit')


class BaseSlotAdminInline(StateMachineAdminMixin, StackedInline):
    model = ActivitySlot
    extra = 0

    raw_id_fields = ('location',)

    can_delete = True
    readonly_fields = ('link', 'created', 'activity')
    fields = (
        'link',
        'start',
        'duration',
        'created',
        'status',
        'states',
        'is_online',
        'location',
        'location_hint',
        'online_meeting_url'
    )

    def link(self, obj):
        url = reverse(
            "admin:{}_{}_change".format(obj._meta.app_label, obj._meta.model_name),
            args=(obj.id,)
        )
        return format_html('<a href="{}">{}</a>', url, obj)
    link.short_description = _('Edit')

    verbose_name = _('Time, date & location')
    verbose_name_plural = _('Time, date & location')

    def status_label(self, obj):
        return obj.states.current_state.name
    status_label.short_description = _('Status')

    def has_add_permission(self, request, obj):
        return True

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


class ScheduleSlotAdminInline(BaseSlotAdminInline):
    model = ScheduleSlot


class TeamScheduleSlotAdminInline(BaseSlotAdminInline):
    model = TeamScheduleSlot


@admin.register(Team)
class TeamAdmin(PolymorphicInlineSupportMixin, RegionManagerAdminMixin, StateMachineAdmin):
    model = Team
    list_display = ('user', 'created', 'activity')
    readonly_fields = ('activity', 'created', 'invite_code', 'registration_info')
    fields = (
        'activity',
        'user',
        'name', 'description', 'registration_info',
        'status', 'states', 'created', 'invite_code'
    )
    raw_id_fields = ('user', 'registration', 'activity')
    inlines = [TeamMemberAdminInline]

    list_filter = [StateMachineFilter]
    office_subregion_path = 'activity__office_location__subregion'

    def get_inlines(self, request, obj):
        inlines = super().get_inlines(request, obj)
        if obj and obj.id and obj.activity and isinstance(obj.activity, ScheduleActivity):
            return inlines + [TeamScheduleSlotAdminInline]
        return inlines

    superadmin_fields = ['force_status']

    def get_fieldsets(self, request, obj=None):
        fields = self.get_fields(request, obj)
        fieldsets = (
            (_('Details'), {'fields': fields}),
        )
        if request.user.is_superuser:
            fieldsets += (
                (_('Super admin'), {'fields': self.superadmin_fields}),
            )
        return fieldsets

    def registration_info(self, obj):
        url = reverse(
            "admin:{}_{}_change".format(
                obj.registration._meta.app_label, obj.registration._meta.model_name
            ),
            args=(obj.registration.id,),
        )

        status = obj.registration.states.current_state.name
        if obj.registration.status == "new":
            template = loader.get_template("admin/time_based/team_registration_info.html")
            return template.render({"status": status, "url": url})
        else:
            title = _("Change review")
            return format_html(
                'Current status <b>{status}</b>. <a href="{url}">{title}</a>',
                url=url,
                status=status,
                title=title,
            )

    registration_info.short_description = _('Registration')


class TeamAdminInline(TabularInlinePaginated):
    model = Team
    readonly_fields = ('link', 'created', 'status_label', 'team_members_count')
    raw_id_fields = ('user', 'registration')
    fields = ('link', 'user', 'status_label', 'team_members_count')

    def link(self, obj):
        url = reverse('admin:time_based_team_change', args=(obj.id,))
        return format_html('<a href="{}">{}</a>', url, obj)

    def has_change_permission(self, request, obj=None):
        return False

    def status_label(self, obj):
        if obj.registration.status != 'accepted':
            return obj.registration.states.current_state.name
        return obj.states.current_state.name

    status_label.short_description = _('Status')

    can_delete = True

    def has_delete_permission(self, request, obj=None):
        return True

    def team_members_count(self, obj):
        return obj.team_members.filter(status='active').count()
    team_members_count.short_description = _('Members')


class PeriodicParticipantAdminInline(BaseContributorInline):
    model = PeriodicParticipant
    verbose_name = _("Participation")
    verbose_name_plural = _("Participation")
    readonly_fields = ['edit', 'start', 'end', 'status_label']
    fields = readonly_fields

    def start(self, obj):
        return obj.slot.start.date()

    def end(self, obj):
        return obj.slot.end.date()


class BaseRegistrationAdminInline(TabularInlinePaginated):
    verbose_name = _("Participant")
    verbose_name_plural = _("Participants")

    readonly_fields = ('status_label', 'edit')
    fields = ('edit', 'user', 'status_label',)
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

    def has_delete_permission(self, request, obj=None):
        return True

    can_delete = True

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
    skip_on_duplicate = TimeBasedAdmin.skip_on_duplicate + [BaseScheduleSlot, Team]

    def get_inlines(self, request, obj):
        inlines = super().get_inlines(request, obj)
        if obj and obj.id:
            # get the stored object, so you can switch between teams/individuals
            # without getting a form error, because of switching inlines
            stored = ScheduleActivity.objects.get(id=obj.id)
            if stored.team_activity == 'teams':
                return (
                    TeamAdminInline,
                    TeamScheduleParticipantAdminInline,
                ) + inlines
            else:
                return (ScheduleParticipantAdminInline,) + inlines
        return inlines

    raw_id_fields = TimeBasedAdmin.raw_id_fields + ['location']
    readonly_fields = TimeBasedAdmin.readonly_fields

    def team_registration_warning(self, obj):
        return admin_info_box(
            _(
                "You can't change between teams/individuals anymore because there are already registrations."
            )
        )

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if obj and obj.registrations.count():
            fields = tuple(fields) + ("team_activity", "team_registration_warning")
        return fields

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
        'duration',
        'is_online',
        'location',
        'location_hint',
        'online_meeting_url',
    ]

    registration_fields = ("team_activity", "capacity",) + TimeBasedAdmin.registration_fields

    def get_registration_fields(self, request, obj):
        fields = self.registration_fields
        if obj and obj.registrations.count():
            fields = ("team_registration_warning",) + fields
        return fields

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        fieldsets.insert(2, (
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

    participant_count.short_description = _("Participants/Teams")


@admin.register(PeriodicSlot)
class PeriodicSlotAdmin(RegionManagerAdminMixin, StateMachineAdmin):
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
class ScheduleSlotAdmin(RegionManagerAdminMixin, StateMachineAdmin):

    list_display = ("start", "duration", "activity", "participant")
    raw_id_fields = ('activity', "location")
    readonly_fields = ("activity", "participant")
    fields = readonly_fields + (
        "status",
        "states",
        "start",
        "duration",
        "is_online",
        "location",
        "location_hint",
        "online_meeting_url"
    )

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

    def participant(self, obj):
        participant = obj.participants.first()
        url = reverse('admin:time_based_scheduleparticipant_change', args=(participant.id,))
        return format_html("<a href='{}'>{}</a>", url, participant)

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if request.user.is_superuser:
            fieldsets += ((_("Super admin"), {"fields": ("force_status", "states")}),)
        return fieldsets


@admin.register(TeamScheduleSlot)
class TeamScheduleSlotAdmin(ScheduleSlotAdmin):
    inlines = [TeamScheduleParticipantAdminInline]
    list_display = ("start", "duration", "activity", "participant_count")
    raw_id_fields = ScheduleSlotAdmin.raw_id_fields + ('team', )
    readonly_fields = ('activity', 'team', )
    fields = readonly_fields + (
        "status",
        "states",
        "start",
        "duration",
        "is_online",
        "location",
        "location_hint",
        "online_meeting_url"
    )

    def participant_count(self, obj):
        return obj.accepted_participants.count()


class PeriodicSlotAdminInline(TabularInlinePaginated):
    model = PeriodicSlot
    verbose_name = _("Slot")
    verbose_name_plural = _("Slots")
    readonly_fields = ("edit", "start_date", "end_date", "duration_readable", "participant_count", "status_label")
    fields = readonly_fields
    ordering = ["-start"]

    def participant_count(self, obj):
        return obj.accepted_participants.count()

    participant_count.short_description = _('Participants')

    def start_date(self, obj):
        return obj.start.date()
    start_date.short_description = _('Start')

    def end_date(self, obj):
        return obj.end.date()
    end_date.short_description = _('End')

    def duration_readable(self, obj):
        return get_human_readable_duration(str(obj.duration)).lower()
    duration_readable.short_description = _('Hours')

    def current_status(self, obj):
        return obj.states.current_state.name

    current_status.short_description = _("Status")

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj):
        return True

    can_delete = True

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
    skip_on_duplicate = TimeBasedAdmin.skip_on_duplicate + [
        PeriodicSlot,
    ]

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
        fieldsets.insert(2, (
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
        help_text=_(
            'This is the date the time slots will repeat until. '
            'Allow for a long loading time if more than 20 time blocks have to be created.'
        ),
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
        interval_day = _('Daily')
        interval_week = _('Weekly on the  {weekday}').format(
            weekday=start.strftime('%A')
        )
        interval_month = _('Monthly on the {nth} {weekday}').format(
            nth=ordinalize(nth_weekday(start)),
            weekday=start.strftime('%A')
        )
        interval_monthday = _('Monthly on the {monthday}').format(
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
            'Options here are based on when this time slot takes place - {start}'
        ).format(start=start.strftime('%A %-d %B %Y %H:%M %Z'))


class SlotBulkAddForm(forms.Form):
    emails = forms.CharField(
        label=_('Emails'),
        help_text=_(
            'Separate the email addresses by commas, one per '
            'line or copy & paste a column from a spreadsheet.'
        ),
        widget=forms.Textarea
    )

    send_messages = forms.BooleanField(
        label=_('Send messages'),
        help_text=_('Email participants that they have been added to this slot.'),
        initial=True
    )

    title = _('Bulk add participants')

    def __init__(self, data=None, *args, **kwargs):
        if data:
            super(SlotBulkAddForm, self).__init__(data)
        else:
            super(SlotBulkAddForm, self).__init__()


@admin.register(DateActivitySlot)
class DateSlotAdmin(BulkAddMixin, SlotAdmin):
    model = DateActivitySlot
    inlines = [SlotParticipantInline, MessageAdminInline]
    save_as = True

    date_hierarchy = 'start'
    list_display = [
        "__str__",
        "start",
        "activity_link",
        "attendee_limit",
        "participants",
        "duration_string",
    ]
    list_filter = [
        'status',
        SlotTimeFilter,
    ]

    def attendee_limit(self, obj):
        return obj.capacity or obj.activity.capacity

    def participants(self, obj):
        return obj.accepted_participants.count()

    participants.short_description = _('Accepted participants')

    detail_fields = SlotAdmin.detail_fields + [
        'title',
        'capacity',
        'start',
        'duration',
    ]

    def get_urls(self):
        urls = super(DateSlotAdmin, self).get_urls()

        extra_urls = [
            re_path(
                r'^(?P<pk>\d+)/duplicate/$',
                self.admin_site.admin_view(self.duplicate_slot),
                name='time_based_dateactivityslot_duplicate'
            )
        ]
        return extra_urls + urls

    def duplicate_slot(self, request, pk, *args, **kwargs):
        slot = DateActivitySlot.objects.get(pk=pk)
        if request.method == "POST":
            form = SlotDuplicateForm(data=request.POST, slot=slot)
            if form.is_valid():
                data = form.cleaned_data
                dates = duplicate_slot(slot, data['interval'], data['end'])
                messages.success(
                    request,
                    _('%(dates)s time slots created' % {'dates': len(dates)})
                )

                slot_overview = reverse('admin:time_based_dateactivity_change', args=(slot.activity.pk,))
                return HttpResponseRedirect(slot_overview + '#/tab/inline_0/')

        if slot.location:
            start = slot.start.astimezone(timezone(slot.location.timezone))
        else:
            start = slot.start

        settings = MemberPlatformSettings.load()

        context = {
            'opts': self.model._meta,
            'slot': slot,
            'time': start.strftime('%H:%M %Z'),
            'form': SlotDuplicateForm(slot=slot),
            'closed': settings.closed
        }
        return TemplateResponse(
            request, 'admin/time_based/duplicate_slot.html', context
        )

    bulk_add_form = SlotBulkAddForm
    bulk_add_template = 'admin/time_based/bulk_add.html'


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

    inlines = ContributorChildAdmin.inlines + (
        ParticipantSlotInline,
        TimeContributionInlineAdmin
    )
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

    inlines = ContributorChildAdmin.inlines + (
        TimeContributionInlineAdmin,
    )
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

    inlines = ContributorChildAdmin.inlines + (
        TimeContributionInlineAdmin,
    )

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


class SlotForeignKeyRawIdWidget(ForeignKeyRawIdWidget):

    def __init__(self, rel, admin_site, attrs=None, using=None):
        attrs['class'] = 'slot-selector'
        super().__init__(rel, admin_site, attrs, using)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        rel_to = self.rel.model
        if value:
            related_url = reverse(
                'admin:%s_%s_change' % (
                    rel_to._meta.app_label,
                    rel_to._meta.model_name,
                ),
                current_app=self.admin_site.name,
                args=(value,)
            )
            context['related_url'] = related_url
            context['link_label'] = _('View slot')
        else:
            related_url = reverse(
                'admin:%s_%s_add' % (
                    rel_to._meta.app_label,
                    rel_to._meta.model_name,
                ),
                current_app=self.admin_site.name,
            )
            params = {}
            parent = self.attrs.get('parent')
            if parent:
                params = {
                    'activity': parent.activity.id,
                    'duration': parent.activity.duration,
                    'is_online': parent.activity.is_online,
                    'location_hint': parent.activity.location_hint,
                    'online_meeting_url': parent.activity.online_meeting_url,
                    '_to_field': 'id',
                    '_popup': 1,

                }
                if parent.activity.location:
                    params['location'] = parent.activity.location.id
            context['related_url'] = related_url + '?' + urlencode(params)
            context['link_label'] = _('Create slot')
        return context


@admin.register(ScheduleParticipant)
class ScheduleParticipantAdmin(ContributorChildAdmin):

    inlines = ContributorChildAdmin.inlines + (TimeContributionInlineAdmin, )

    fields = ContributorChildAdmin.fields + ["registration_info", "slot_info"]
    pending_fields = ["activity", "user", "registration_info", "created", "updated"]

    def get_fields(self, request, obj=None):
        if obj and obj.registration and obj.registration.status == "new":
            return self.pending_fields
        return self.fields

    readonly_fields = ContributorChildAdmin.readonly_fields + [
        "activity", "created", "updated",
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

    registration_info.short_description = _('Registration')

    def slot_info(self, obj):
        if not obj.slot:
            return "- no slot set -"
        url = reverse("admin:time_based_scheduleslot_change", args=(obj.slot.id,))
        if obj.slot.start:
            return format_html(
                "<div style='display:inline-block'>{}<br/>{} - {} <br/>{}<br/><a href='{}'>Edit</a></span>",
                obj.slot.start.date(),
                obj.slot.start.time(),
                obj.slot.end.time(),
                obj.slot.is_online and _("Remote/Online") or obj.slot.location,
                url,
            )
        return format_html(
            "<a href='{}'>- no time set -</a>",
            url,
        )
    slot_info.short_description = _('Date, Time & Location')

    list_display = ['__str__', 'activity_link', 'status']


@admin.register(TeamScheduleParticipant)
class TeamScheduleParticipantAdmin(ScheduleParticipantAdmin):
    model = TeamScheduleParticipant
    readonly_fields = ScheduleParticipantAdmin.readonly_fields + ["slot", "team_member"]
    fields = ContributorChildAdmin.fields + ["registration_info", "slot", "team_member"]


@admin.register(Registration)
class RegistrationAdmin(PolymorphicParentModelAdmin, StateMachineAdmin):
    base_model = Registration
    child_models = (
        PeriodicRegistration,
        DeadlineRegistration,
        ScheduleRegistration,
        TeamScheduleRegistration,
    )
    list_display = ['created', 'user', 'type', 'activity', 'state_name']
    list_filter = (PolymorphicChildModelFilter, StateMachineFilter,)
    date_hierarchy = 'created'
    ordering = ('-created',)

    def type(self, obj):
        return obj.get_real_instance_class()._meta.verbose_name


class RegistrationChildAdmin(PolymorphicInlineSupportMixin, PolymorphicChildModelAdmin, StateMachineAdmin):
    base_model = Registration
    raw_id_fields = ("user",)
    readonly_fields = ["document", "created", "activity"]
    fields = readonly_fields + ["answer", "status", "states"]
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


@admin.register(TeamScheduleRegistration)
class TeamScheduleRegistrationAdmin(RegistrationChildAdmin):
    readonly_fields = RegistrationChildAdmin.readonly_fields + ['team']
    fields = ['team', 'states', 'answer', 'document']
    verbose_name = _('Team registration')
    verbose_name_plural = _('Team registrations')


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

    detail_fields = ['participant', 'slot', 'status', 'states']

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (_('Detail'), {'fields': self.detail_fields}),
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
