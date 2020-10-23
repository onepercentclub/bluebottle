from django.contrib import admin

from bluebottle.fsm.admin import StateMachineFilter
from bluebottle.activities.admin import ActivityChildAdmin
from bluebottle.time_based.models import (
    OnADateActivity, WithADeadlineActivity, OngoingActivity
)
from bluebottle.notifications.admin import MessageAdminInline
from bluebottle.utils.admin import export_as_csv_action


class TimeBasedAdmin(ActivityChildAdmin):
    inlines = ActivityChildAdmin.inlines + (MessageAdminInline, )

    search_fields = ['title', 'description']
    list_filter = [StateMachineFilter, 'is_online']

    detail_fields = ActivityChildAdmin.detail_fields + (
        'capacity',
        'duration',
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


@admin.register(OnADateActivity)
class OnADateActivityAdmin(TimeBasedAdmin):
    base_model = OnADateActivity

    date_hierarchy = 'start'
    list_display = TimeBasedAdmin.list_display + [
        'start', 'duration',
    ]

    detail_fields = TimeBasedAdmin.detail_fields + (
        'start',
        'duration'
    )

    export_as_csv_fields = TimeBasedAdmin.export_to_csv_fields + (
        ('start', 'Start'),
        ('duration', 'Duration'),
    )
    actions = [export_as_csv_action(fields=export_as_csv_fields)]


@admin.register(WithADeadlineActivity)
class WithADeadlineActivityAdmin(TimeBasedAdmin):
    base_model = WithADeadlineActivity

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


@admin.register(OngoingActivity)
class OngoingActivityAdmin(TimeBasedAdmin):
    base_model = OngoingActivity

    list_display = TimeBasedAdmin.list_display + [
        'duration', 'duration_period'
    ]

    detail_fields = TimeBasedAdmin.detail_fields + (
        'start',
        'duration',
        'duration_period',
    )

    export_as_csv_fields = TimeBasedAdmin.export_to_csv_fields + (
        ('duration', 'Duration'),
        ('duration_period', 'Duration period'),
    )
    actions = [export_as_csv_action(fields=export_as_csv_fields)]
