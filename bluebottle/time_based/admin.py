from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from durationwidget.widgets import TimeDurationWidget

from bluebottle.activities.admin import ActivityChildAdmin, IntentionChildAdmin
from bluebottle.fsm.admin import StateMachineFilter, StateMachineAdmin
from bluebottle.notifications.admin import MessageAdminInline
from bluebottle.time_based.models import (
    DateActivity, PeriodActivity, OnADateApplication, PeriodApplication, Application, Duration
)
from bluebottle.utils.admin import export_as_csv_action


class BaseApplicationAdminInline(admin.TabularInline):
    model = Application
    readonly_fields = ('intention_date', 'motivation', 'document', 'edit', 'created', 'transition_date', 'status')
    raw_id_fields = ('user', 'document')
    extra = 0

    def edit(self, obj):
        if not obj.id:
            return '-'
        return format_html(
            '<a href="{}">{}</a>',
            reverse(
                'admin:time_based_{}_change'.format(obj.__class__.__name__.lower()),
                args=(obj.id,)),
            _('Edit application')
        )


class OnADateApplicationAdminInline(BaseApplicationAdminInline):
    model = OnADateApplication


class PeriodApplicationAdminInline(BaseApplicationAdminInline):
    model = PeriodApplication
    readonly_fields = BaseApplicationAdminInline.readonly_fields + ('current_period', )


class TimeBasedAdmin(ActivityChildAdmin):
    inlines = ActivityChildAdmin.inlines + (MessageAdminInline, )

    search_fields = ['title', 'description']
    list_filter = [StateMachineFilter, 'is_online']

    detail_fields = ActivityChildAdmin.detail_fields + (
        'capacity',
        'is_online',
        'location',
        'location_hint',
        'review',
        'registration_deadline',
    )

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
        ('review', 'Review applications')
    )


@admin.register(DateActivity)
class DateActivityAdmin(TimeBasedAdmin):
    base_model = DateActivity

    inlines = (OnADateApplicationAdminInline, ) + TimeBasedAdmin.inlines

    date_hierarchy = 'start'
    list_display = TimeBasedAdmin.list_display + [
        'start', 'duration',
    ]

    detail_fields = TimeBasedAdmin.detail_fields + (
        'start',
        'duration',
        'online_meeting_url'
    )

    export_as_csv_fields = TimeBasedAdmin.export_to_csv_fields + (
        ('start', 'Start'),
        ('duration', 'Duration'),
    )
    actions = [export_as_csv_action(fields=export_as_csv_fields)]


@admin.register(PeriodActivity)
class PeriodActivityAdmin(TimeBasedAdmin):
    base_model = PeriodActivity
    formfield_overrides = {
        models.DurationField: {
            'widget': TimeDurationWidget(
                show_days=False,
                show_hours=True,
                show_minutes=True,
                show_seconds=False)
        }
    }

    inlines = (PeriodApplicationAdminInline, ) + TimeBasedAdmin.inlines

    date_hierarchy = 'deadline'
    list_display = TimeBasedAdmin.list_display + [
        'deadline', 'duration', 'duration_period'
    ]

    detail_fields = TimeBasedAdmin.detail_fields + (
        'start',
        'deadline',
        'duration',
        'duration_period',
    )

    export_as_csv_fields = TimeBasedAdmin.export_to_csv_fields + (
        ('deadline', 'Deadline'),
        ('duration', 'Duration'),
        ('duration_period', 'Duration period'),
    )
    actions = [export_as_csv_action(fields=export_as_csv_fields)]


class DurationInlineAdmin(admin.TabularInline):
    model = Duration
    extra = 0
    readonly_fields = ('edit', 'status', 'created')

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


@admin.register(PeriodApplication)
class PeriodApplicationAdmin(IntentionChildAdmin):
    inlines = IntentionChildAdmin.inlines + [DurationInlineAdmin]


@admin.register(Duration)
class DurationAdmin(StateMachineAdmin):
    raw_id_fields = ('intention',)
    readonly_fields = ('status', 'created', )
    basic_fields = ('intention', 'created', 'start', 'end', 'value', 'status', 'states')

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (_('Basic'), {'fields': self.basic_fields}),
        )
        if request.user.is_superuser:
            fieldsets += (
                (_('Super admin'), {'fields': (
                    'force_status',
                )}),
            )
        return fieldsets


@admin.register(OnADateApplication)
class DateApplicationAdmin(IntentionChildAdmin):
    fields = IntentionChildAdmin.fields
