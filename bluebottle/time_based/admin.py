from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from bluebottle.fsm.admin import StateMachineFilter
from bluebottle.activities.admin import ActivityChildAdmin
from bluebottle.time_based.models import (
    DateActivity, PeriodActivity, OnADateApplication, PeriodApplication, Application
)
from bluebottle.notifications.admin import MessageAdminInline
from bluebottle.utils.admin import export_as_csv_action
from django.utils.translation import ugettext_lazy as _


class BaseApplicationAdminInline(admin.TabularInline):
    model = Application
    readonly_fields = ('edit', 'created', 'transition_date', 'status')
    raw_id_fields = ('user', 'document')
    extra = 0

    def edit(self, obj):
        return
        if not obj.id:
            return '-'
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:time_based_application_change', args=(obj.id,)),
            _('Edit participant')
        )


class OnADateApplicationAdminInline(BaseApplicationAdminInline):
    model = OnADateApplication


class PeriodApplicationAdminInline(BaseApplicationAdminInline):
    model = PeriodApplication


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
