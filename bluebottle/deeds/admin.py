from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from bluebottle.activities.admin import (
    ActivityChildAdmin, ContributorChildAdmin, TeamInline, BaseContributorInline
)
from bluebottle.activities.models import EffortContribution
from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.follow.admin import FollowAdminInline
from bluebottle.updates.admin import UpdateInline
from bluebottle.utils.admin import export_as_csv_action, admin_info_box


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


class DeedParticipantInline(BaseContributorInline):
    model = DeedParticipant
    verbose_name = _("Participant")
    verbose_name_plural = _("Participants")


@admin.register(Deed)
class DeedAdmin(ActivityChildAdmin):
    base_model = Deed
    inlines = (TeamInline, DeedParticipantInline, UpdateInline, FollowAdminInline)
    list_filter = ['status']
    search_fields = ['title', 'description']
    readonly_fields = ActivityChildAdmin.readonly_fields + ['team_activity', 'next_step_info']
    list_display = ActivityChildAdmin.list_display + [
        'start',
        'end',
        'enable_impact',
        'target',
        'participant_count',
    ]
    save_as = True

    def participant_count(self, obj):
        return obj.participants.count() + obj.deleted_successful_contributors or 0
    participant_count.short_description = _('Participants')

    def next_step_info(self, obj):
        return admin_info_box(
            _('Redirect participants to an external website so '
              'they can complete an action such as registering a vote.')
        )

    registration_fields = (
        'start',
        'end',
        'target',
        'next_step_info',
        'next_step_title',
        'next_step_description',
        'next_step_button_label',
        'next_step_link',

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
