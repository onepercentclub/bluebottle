from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_admin_inline_paginator.admin import TabularInlinePaginated
from django_summernote.widgets import SummernoteWidget

from bluebottle.activities.admin import (
    ActivityChildAdmin, ContributorChildAdmin, ActivityForm, TeamInline
)
from bluebottle.activities.models import EffortContribution
from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.utils.admin import export_as_csv_action


class DeedAdminForm(ActivityForm):
    class Meta(object):
        model = Deed
        fields = '__all__'
        widgets = {
            'description': SummernoteWidget(attrs={'height': 400})
        }


class EffortContributionInlineAdmin(admin.TabularInline):
    model = EffortContribution
    extra = 0
    readonly_fields = ('contribution_type', 'status', 'start',)
    fields = readonly_fields


@admin.register(DeedParticipant)
class DeedParticipantAdmin(ContributorChildAdmin):
    readonly_fields = ['created']
    raw_id_fields = ['user', 'activity']
    fields = ['activity', 'user', 'status', 'states'] + readonly_fields
    list_display = ['__str__', 'activity_link', 'status']
    inlines = ContributorChildAdmin.inlines + [EffortContributionInlineAdmin]


class DeedParticipantInline(TabularInlinePaginated):
    model = DeedParticipant
    per_page = 20
    ordering = ['-created']
    raw_id_fields = ['user']
    readonly_fields = ['edit', 'created', 'status']
    fields = ['edit', 'user', 'created', 'status']
    extra = 0
    # template = 'admin/participant_list.html'

    def edit(self, obj):
        if not obj.user and obj.activity.has_deleted_data:
            return format_html(f'<i>{_("Anonymous")}</i>')
        url = reverse('admin:deeds_deedparticipant_change', args=(obj.id,))
        return format_html('<a href="{}">{}</a>', url, _('Edit participant'))
    edit.short_description = _('Edit participant')

    def get_readonly_fields(self, request, obj=None):
        fields = self.readonly_fields
        if obj.has_deleted_data:
            fields += ('user',)
        return fields


@admin.register(Deed)
class DeedAdmin(ActivityChildAdmin):
    base_model = Deed
    form = DeedAdminForm
    inlines = (TeamInline, DeedParticipantInline,) + ActivityChildAdmin.inlines
    list_filter = ['status']
    search_fields = ['title', 'description']
    readonly_fields = ActivityChildAdmin.readonly_fields + ['team_activity']
    list_display = ActivityChildAdmin.list_display + [
        'start',
        'end',
        'enable_impact',
        'target',
        'participant_count',
    ]

    def participant_count(self, obj):
        return obj.participants.count() + obj.deleted_successful_contributors or 0
    participant_count.short_description = _('Participants')

    detail_fields = ActivityChildAdmin.detail_fields + (
        'start',
        'end',
        'enable_impact',
        'target',
    )

    export_as_csv_fields = (
        ('title', 'Title'),
        ('description', 'Description'),
        ('status', 'Status'),
        ('created', 'Created'),
        ('initiative__title', 'Initiative'),
        ('registration_deadline', 'Registration Deadline'),
        ('owner__full_name', 'Owner'),
        ('owner__email', 'Email'),
        ('office_location', 'Office Location'),
        ('start', 'Start'),
        ('end', 'End'),
    )

    actions = [export_as_csv_action(fields=export_as_csv_fields)]
