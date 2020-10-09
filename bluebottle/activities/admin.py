from django.conf.urls import url
from django.contrib import admin
from django.http.response import HttpResponseRedirect, HttpResponseForbidden
from django.template import loader
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from polymorphic.admin import (
    PolymorphicParentModelAdmin, PolymorphicChildModelAdmin, PolymorphicChildModelFilter,
    StackedPolymorphicInline)

from bluebottle.activities.forms import ImpactReminderConfirmationForm
from bluebottle.activities.messages import ImpactReminderMessage
from bluebottle.activities.models import Activity, Contribution, Organizer
from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.bluebottle_dashboard.decorators import confirmation_form
from bluebottle.events.models import Event, Participant
from bluebottle.follow.admin import FollowAdminInline
from bluebottle.fsm.admin import StateMachineAdmin, StateMachineFilter
from bluebottle.funding.models import Funding, Donation
from bluebottle.impact.admin import ImpactGoalInline
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.segments.models import Segment
from bluebottle.wallposts.admin import WallpostInline


class ContributionChildAdmin(PolymorphicChildModelAdmin, StateMachineAdmin):
    base_model = Contribution
    search_fields = ['user__first_name', 'user__last_name', 'activity__title']
    list_filter = [StateMachineFilter, ]
    ordering = ('-created', )
    show_in_index = True

    readonly_fields = [
        'contribution_date',
        'created',
        'activity_link',
    ]

    fields = ['activity', 'user', 'states', 'status'] + readonly_fields
    superadmin_fields = ['force_status']

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (_('Basic'), {'fields': self.fields}),
        )
        if request.user.is_superuser:
            fieldsets += (
                (_('Super admin'), {'fields': self.superadmin_fields}),
            )
        return fieldsets

    def activity_link(self, obj):
        url = reverse("admin:{}_{}_change".format(
            obj.activity._meta.app_label,
            obj.activity._meta.model_name),
            args=(obj.activity.id,)
        )
        return format_html(u"<a href='{}'>{}</a>", url, obj.activity.title or '-empty-')
    activity_link.short_description = _('Activity')


@admin.register(Organizer)
class OrganizerAdmin(ContributionChildAdmin):
    model = Organizer
    list_display = ['user', 'status', 'activity_link']
    raw_id_fields = ('user', 'activity')

    readonly_fields = ContributionChildAdmin.readonly_fields + \
        ['status', 'created', 'transition_date']

    date_hierarchy = 'contribution_date'

    export_to_csv_fields = (
        ('status', 'Status'),
        ('created', 'Created'),
        ('activity', 'Activity'),
        ('user__full_name', 'Owner'),
        ('user__email', 'Email'),
        ('contribution_date', 'Contribution Date'),
    )


@admin.register(Contribution)
class ContributionAdmin(PolymorphicParentModelAdmin, StateMachineAdmin):
    base_model = Contribution
    child_models = (Participant, Donation, Applicant, Organizer)
    list_display = ['created', 'contribution_date',
                    'owner', 'type', 'activity', 'state_name']
    list_filter = (PolymorphicChildModelFilter, StateMachineFilter,)
    date_hierarchy = 'contribution_date'

    ordering = ('-created', )

    def type(self, obj):
        return obj.get_real_instance_class()._meta.verbose_name


class ActivityChildAdmin(PolymorphicChildModelAdmin, StateMachineAdmin):
    base_model = Activity
    raw_id_fields = ['owner', 'initiative']
    inlines = (FollowAdminInline, WallpostInline, )

    def get_inline_instances(self, request, obj=None):
        inlines = super(ActivityChildAdmin,
                        self).get_inline_instances(request, obj)

        if InitiativePlatformSettings.objects.get().enable_impact:
            impact_goal_inline = ImpactGoalInline(self.model, self.admin_site)
            if (
                impact_goal_inline.has_add_permission(request) and
                impact_goal_inline.has_change_permission(request, obj) and
                impact_goal_inline.has_delete_permission(request, obj)
            ):
                inlines.append(impact_goal_inline)

        return inlines

    show_in_index = True

    ordering = ('-created', )

    readonly_fields = [
        'created',
        'updated',
        'valid',
        'transition_date',
        'stats_data',
        'review_status',
        'send_impact_reminder_message_link',
    ]

    basic_fields = (
        'title',
        'slug',
        'image',
        'video_url',
        'initiative',
        'owner',
        'created',
        'updated',
        'stats_data',
    )

    def get_status_fields(self, request, obj):
        fields = ('status', 'states', )

        if obj and obj.status in ('draft', 'submitted', 'needs_work'):
            fields = ('valid', ) + fields

        return fields

    def get_detail_fields(self, request, obj):
        fields = self.detail_fields

        if Segment.objects.filter(type__is_active=True).count():
            fields = fields + ('segments',)

        if (
            obj and
            obj.status in ('succeeded', 'partially_funded') and
            InitiativePlatformSettings.objects.get().enable_impact
        ):
            fields = fields + ('send_impact_reminder_message_link', )

        return fields

    detail_fields = (
        'description',
        'highlight'
    )

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (_('Basic'), {'fields': self.basic_fields}),
            (_('Details'), {'fields': self.get_detail_fields(request, obj)}),
            (_('Status'), {'fields': self.get_status_fields(request, obj)}),
        )
        if request.user.is_superuser:
            fieldsets += (
                (_('Super admin'), {'fields': (
                    'force_status',
                )}),
            )
        return fieldsets

    def stats_data(self, obj):
        template = loader.get_template(
            'admin/activity-stats.html'
        )

        return template.render({'stats': obj.stats})
    stats_data.short_description = _('Statistics')

    def valid(self, obj):
        errors = list(obj.errors)
        required = list(obj.required)
        if not errors and obj.states.initiative_is_approved() and not required:
            return '-'

        errors += [
            _("{} is required").format(obj._meta.get_field(field).verbose_name.title())
            for field in required
        ]

        if not obj.states.initiative_is_approved():
            errors.append(_('The initiative is not approved'))

        return format_html("<ul class='validation-error-list'>{}</ul>", format_html("".join([
            format_html(u"<li>{}</li>", value) for value in errors
        ])))

    valid.short_description = _('Steps to complete activity')

    def get_urls(self):
        urls = super(ActivityChildAdmin, self).get_urls()
        extra_urls = [
            url(r'^send-impact-reminder-message/(?P<pk>\d+)/$',
                self.admin_site.admin_view(self.send_impact_reminder_message),
                name='{}_{}_send_impact_reminder_message'.format(
                    self.model._meta.app_label,
                    self.model._meta.model_name
                ),
                )
        ]
        return extra_urls + urls

    @confirmation_form(
        ImpactReminderConfirmationForm,
        Activity,
        'admin/activities/send_impact_reminder_message.html'
    )
    def send_impact_reminder_message(self, request, activity):
        if not request.user.has_perm('{}.change_{}'.format(
                self.model._meta.app_label,
                self.model._meta.model_name
        )):
            return HttpResponseForbidden('Not allowed to change user')

        ImpactReminderMessage(activity).compose_and_send()

        message = _('User {name} will receive a message.').format(
            name=activity.owner.full_name)
        self.message_user(request, message)

        return HttpResponseRedirect(reverse('admin:activities_activity_change', args=(activity.id, )))
    send_impact_reminder_message.short_description = _('impact reminder')

    def send_impact_reminder_message_link(self, obj):
        url = reverse(
            'admin:{}_{}_send_impact_reminder_message'.format(
                self.model._meta.app_label,
                self.model._meta.model_name
            ),
            args=(obj.pk,)
        )
        return format_html(
            u"<a href='{}'>{}</a>",
            url, _('Send reminder message')
        )
    send_impact_reminder_message.short_description = _('Impact Reminder')

    def get_form(self, request, obj=None, **kwargs):
        kwargs.update({
            'help_texts': {
                'send_impact_reminder_message_link': _(
                    u"Request the activity manager to fill in the impact of this activity."
                )
            }
        })
        return super(ActivityChildAdmin, self).get_form(request, obj, **kwargs)


class ContributionInline(admin.TabularInline):
    raw_id_fields = ('user', )
    readonly_fields = ('created', 'edit', 'state_name', )
    fields = ('edit', 'user', 'created', 'state_name', )

    extra = 0

    def state_name(self, obj):
        if obj.states.current_state:
            return obj.states.current_state.name
    state_name.short_description = _('status')

    def edit(self, obj):
        url = reverse(
            'admin:{}_{}_change'.format(
                obj._meta.app_label,
                obj._meta.model_name,
            ),
            args=(obj.id,)
        )
        return format_html('<a href="{}">{}</a>', url, obj.id)
    edit.short_description = _('edit')


@admin.register(Activity)
class ActivityAdmin(PolymorphicParentModelAdmin, StateMachineAdmin):
    base_model = Activity
    child_models = (Event, Funding, Assignment)
    date_hierarchy = 'transition_date'
    readonly_fields = ['link', 'review_status']
    list_filter = (PolymorphicChildModelFilter, StateMachineFilter, 'highlight')
    list_editable = ('highlight',)

    list_display = ['__str__', 'created', 'type', 'state_name',
                    'link', 'highlight']

    search_fields = ('title', 'description',
                     'owner__first_name', 'owner__last_name')

    def link(self, obj):
        return format_html(u'<a href="{}" target="_blank">{}</a>', obj.get_absolute_url(), obj.title)

    link.short_description = _("Show on site")

    ordering = ('-created', )

    def type(self, obj):
        return obj.get_real_instance_class()._meta.verbose_name


class ActivityInlineChild(StackedPolymorphicInline.Child):
    def state_name(self, obj):
        if obj.states.current_state:
            return obj.states.current_state.name
    state_name.short_description = _('status')

    def activity_link(self, obj):
        url = reverse("admin:{}_{}_change".format(
            obj._meta.app_label,
            obj._meta.model_name),
            args=(obj.id,)
        )
        return format_html(u"<a href='{}'>{}</a>", url, obj.title or '-empty-')

    activity_link.short_description = _('Edit activity')

    def link(self, obj):
        return format_html(u'<a href="{}" target="_blank">{}</a>', obj.get_absolute_url(), obj.title or '-empty-')

    link.short_description = _('View on site')


class ActivityAdminInline(StackedPolymorphicInline):
    model = Activity
    readonly_fields = ['title', 'created', 'owner']
    fields = readonly_fields
    extra = 0
    can_delete = False

    class EventInline(ActivityInlineChild):
        readonly_fields = ['activity_link',
                           'link', 'start', 'duration', 'state_name']
        fields = readonly_fields
        model = Event

    class FundingInline(ActivityInlineChild):
        readonly_fields = ['activity_link',
                           'link', 'target', 'deadline', 'state_name']
        fields = readonly_fields
        model = Funding

    class AssignmentInline(ActivityInlineChild):
        readonly_fields = ['activity_link',
                           'link', 'date', 'duration', 'state_name']
        fields = readonly_fields
        model = Assignment

    child_inlines = (
        EventInline,
        FundingInline,
        AssignmentInline
    )
