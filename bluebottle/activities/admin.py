import re

from django import forms
from django.conf.urls import url
from django.contrib import admin, messages
from django.db import connection
from django.http.response import HttpResponseRedirect, HttpResponseForbidden
from django.template import loader
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _, ngettext
from django_admin_inline_paginator.admin import PaginationFormSetBase, TabularInlinePaginated
from polymorphic.admin import (
    PolymorphicParentModelAdmin, PolymorphicChildModelAdmin, PolymorphicChildModelFilter,
    StackedPolymorphicInline, PolymorphicInlineSupportMixin)
from pytz import timezone

from bluebottle.activities.forms import ImpactReminderConfirmationForm
from bluebottle.activities.messages import ImpactReminderMessage
from bluebottle.activities.models import (
    Activity, Contributor, Organizer, Contribution, EffortContribution, Team
)
from bluebottle.activities.utils import bulk_add_participants
from bluebottle.bluebottle_dashboard.decorators import confirmation_form
from bluebottle.collect.models import CollectContributor, CollectActivity
from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.follow.models import Follow
from bluebottle.fsm.admin import StateMachineAdmin, StateMachineFilter
from bluebottle.fsm.forms import StateMachineModelForm, StateMachineModelFormMetaClass
from bluebottle.funding.models import Funding, Donor, MoneyContribution
from bluebottle.geo.models import Location
from bluebottle.impact.admin import ImpactGoalInline
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.notifications.models import Message
from bluebottle.offices.admin import RegionManagerAdminMixin
from bluebottle.segments.models import SegmentType
from bluebottle.time_based.models import (
    DateActivity,
    DeadlineActivity,
    DateParticipant,
    ScheduleActivity,
    TimeContribution,
    DeadlineParticipant,
    PeriodicActivity,
    ScheduleParticipant,
    TeamScheduleParticipant,
    PeriodicParticipant,
)
from bluebottle.updates.admin import UpdateInline
from bluebottle.updates.models import Update
from bluebottle.utils.widgets import get_human_readable_duration


@admin.register(Contributor)
class ContributorAdmin(PolymorphicParentModelAdmin, RegionManagerAdminMixin, StateMachineAdmin):
    base_model = Contributor
    child_models = (
        Donor,
        Organizer,
        DateParticipant,
        DeedParticipant,
        CollectContributor,
        DeadlineParticipant,
        ScheduleParticipant,
        TeamScheduleParticipant,
        PeriodicParticipant,
    )
    list_display = ['created', 'owner', 'type', 'activity', 'state_name']
    list_filter = (PolymorphicChildModelFilter, StateMachineFilter,)
    date_hierarchy = 'created'

    ordering = ('-created',)

    def type(self, obj):
        return obj.get_real_instance_class()._meta.verbose_name


class ContributionInlineChild(StackedPolymorphicInline.Child):
    def state_name(self, obj):
        if obj.states.current_state:
            return obj.states.current_state.name

    state_name.short_description = _('status')
    ordering = ['-created']

    def contributor_link(self, obj):
        url = reverse("admin:{}_{}_change".format(
            obj._meta.app_label,
            obj._meta.model_name),
            args=(obj.id,)
        )
        return format_html(u"<a href='{}'>{}</a>", url, obj.title or '-empty-')

    contributor_link.short_description = _('Edit')


class BaseContributorInline(TabularInlinePaginated):
    model = Contributor
    raw_id_fields = ['user']
    readonly_fields = ['edit', 'created', 'status_label']
    fields = ['edit', 'created', 'user', 'status_label']
    extra = 0
    per_page = 10
    ordering = ['-created']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    template = 'admin/participant_list.html'

    can_delete = True

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    def edit(self, obj):
        if not obj.user and obj.activity.has_deleted_data:
            return format_html(f'<i>{_("Anonymous")}</i>')
        url = reverse('admin:{}_{}_change'.format(
            obj._meta.app_label,
            obj._meta.model_name
        ), args=(obj.id,))
        return format_html('<a href="{}">{}</a>', url, _('Edit'))

    edit.short_description = _('Edit')

    def status_label(self, obj):
        return obj.states.current_state.name


class ContributorChildAdmin(
    PolymorphicInlineSupportMixin, PolymorphicChildModelAdmin,
    RegionManagerAdminMixin, StateMachineAdmin
):
    base_model = Contributor
    search_fields = ['user__first_name', 'user__last_name', 'activity__title']
    list_filter = [StateMachineFilter, ]
    ordering = ('-created',)
    show_in_index = True

    date_hierarchy = 'contributor_date'

    raw_id_fields = ('user',)

    readonly_fields = [
        "activity",
        "transition_date",
        "contributor_date",
        "created",
        "updated",
        "team",
    ]

    fields = [
        "activity",
        "user",
        "states",
        "status",
        "transition_date",
        "contributor_date",
        "created",
        "updated",
        "team",
    ]

    superadmin_fields = ['force_status']

    def get_fieldsets(self, request, obj=None):
        fields = self.get_fields(request, obj)
        if InitiativePlatformSettings.team_activities and 'team' not in fields:
            fields += ('team',)
        fieldsets = (
            (_('Details'), {'fields': fields}),
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

    def type(self, obj):
        return obj.polymorphic_ctype


@admin.register(Organizer)
class OrganizerAdmin(ContributorChildAdmin):
    model = Organizer
    list_display = ['user', 'status', 'activity_link']
    raw_id_fields = ('user', 'activity')

    readonly_fields = ContributorChildAdmin.readonly_fields + ['status', 'created', 'transition_date']

    date_hierarchy = 'created'

    export_to_csv_fields = (
        ('status', 'Status'),
        ('created', 'Created'),
        ('activity', 'Activity'),
        ('user__full_name', 'Owner'),
        ('user__email', 'Email'),
    )


@admin.register(Contribution)
class ContributionAdmin(PolymorphicParentModelAdmin, RegionManagerAdminMixin, StateMachineAdmin):
    base_model = Contribution
    child_models = (
        MoneyContribution,
        TimeContribution,
        EffortContribution
    )
    list_display = ['start', 'contribution_type', 'contributor_link', 'state_name', 'value']
    list_filter = (
        PolymorphicChildModelFilter,
        StateMachineFilter
    )
    date_hierarchy = 'start'

    ordering = ('-start',)

    def lookup_allowed(self, lookup, value):
        if lookup == 'contributor__user_id':
            return True
        return super(ContributionAdmin, self).lookup_allowed(lookup, value)

    def contributor_link(self, obj):
        if obj and obj.contributor_id:
            url = reverse('admin:activities_contributor_change', args=(obj.contributor.id,))
            return format_html('<a href="{}">{}</a>', url, obj.contributor)

    contributor_link.short_description = _('Contributor')

    def contribution_type(self, obj):
        return obj.polymorphic_ctype

    def contributor_type(self, obj):
        return obj.contributor.get_real_instance_class()._meta.verbose_name

    def value(self, obj):
        type = obj.get_real_instance_class().__name__
        if type == 'MoneyContribution':
            return obj.moneycontribution.value
        if type == 'TimeContribution':
            return get_human_readable_duration(str(obj.timecontribution.value)).lower()
        return '-'


class ContributionChildAdmin(PolymorphicChildModelAdmin, RegionManagerAdminMixin, StateMachineAdmin):
    base_model = Contribution
    raw_id_fields = ('contributor',)
    readonly_fields = ['status', 'created', ]

    fields = [
        'contributor',
        'start',
        'status',
        'states',
        'created'
    ]

    superadmin_fields = [
        'force_status',
    ]

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (_('Details'), {'fields': self.fields}),
        )
        if request.user.is_superuser:
            fieldsets += (
                (_('Super admin'), {'fields': self.superadmin_fields}),
            )
        return fieldsets


@admin.register(EffortContribution)
class EffortContributionAdmin(ContributionChildAdmin):
    model = EffortContribution


class ActivityFormMetaClass(StateMachineModelFormMetaClass):
    def __new__(cls, name, bases, attrs):
        if 'Meta' in attrs and connection.tenant.schema_name != 'public':
            for segment_type in SegmentType.objects.all():
                attrs[segment_type.field_name] = forms.ModelMultipleChoiceField(
                    required=False,
                    label=segment_type.name,
                    queryset=segment_type.segments,
                )

        return super().__new__(cls, name, bases, attrs)


class ActivityForm(StateMachineModelForm, metaclass=ActivityFormMetaClass):
    def __init__(self, *args, **kwargs):
        super(ActivityForm, self).__init__(*args, **kwargs)
        f = self.fields.get('user_permissions', None)
        if f is not None:
            f.queryset = f.queryset.select_related('content_type')

        if connection.tenant.schema_name != 'public':
            for segment_type in SegmentType.objects.all():
                if self.instance.pk:
                    self.initial[segment_type.field_name] = self.instance.segments.filter(
                        segment_type=segment_type).all()


class TeamInline(admin.TabularInline):
    model = Team
    raw_id_fields = ('owner',)
    readonly_fields = ('team_link', 'slot_link', 'created', 'status')
    fields = readonly_fields + ('owner',)

    extra = 0
    ordering = ['slot__start']

    def team_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:activities_team_change', args=(obj.id,)),
            obj
        )

    team_link.short_description = _('Edit')

    def slot_link(self, obj):
        if getattr(obj, 'slot', None):
            if obj.slot.location:
                return format_html(
                    '<a href="{}#/tab/inline_1/">{}</a>',
                    reverse('admin:activities_team_change', args=(obj.id,)),
                    obj.slot.start.astimezone(timezone(obj.slot.location.timezone)).strftime('%c')
                )
            else:
                return format_html(
                    '<a href="{}#/tab/inline_1/">{}</a>',
                    reverse('admin:activities_team_change', args=(obj.id,)),
                    obj.slot.start.strftime('%c')
                )
        return format_html(
            '<a href="{}#/tab/inline_1/">{}</a>',
            reverse('admin:activities_team_change', args=(obj.id,)),
            _('Add time slot')
        )

    slot_link.short_description = _('Time slot')


class ActivityBulkAddForm(forms.Form):
    emails = forms.CharField(
        label=_('Emails'),
        help_text=_('Enter the email addresses of the participants you want to add to this activity.'),
        widget=forms.Textarea
    )

    send_messages = forms.BooleanField(
        label=_('Send messages'),
        help_text=_('Notify the participants that they have been added to this activity.'),
        initial=True
    )

    title = _('Bulk add participants')

    def __init__(self, activity, data=None, *args, **kwargs):
        if data:
            super(ActivityBulkAddForm, self).__init__(data)
        else:
            super(ActivityBulkAddForm, self).__init__()

    class Media:
        css = {
            'all': ('checkbox.css',)
        }


class ActivityChildAdmin(PolymorphicChildModelAdmin, RegionManagerAdminMixin, StateMachineAdmin):
    base_model = Activity
    raw_id_fields = ['owner', 'initiative', 'office_location']
    inlines = (UpdateInline,)
    form = ActivityForm

    skip_on_duplicate = [Contributor, Follow, Message, Update]

    def get_formsets_with_inlines(self, request, obj=None):
        formsets = super().get_formsets_with_inlines(request, obj)

        if "_saveasnew" in request.POST:
            formsets = [
                (inline, formset)
                for (inline, formset) in formsets
                if not any(
                    issubclass(formset.model, skipped_model)
                    for skipped_model in self.skip_on_duplicate
                )
            ]

        return formsets

    def lookup_allowed(self, key, value):
        if key in [
            'office_location__id__exact',
            'office_location__subregion__id__exact',
            'office_location__subregion__region__id__exact',
        ]:
            return True
        return super(ActivityChildAdmin, self).lookup_allowed(key, value)

    def save_model(self, request, obj, form, change):
        if obj.states.transitions['auto_submit'] in obj.states.possible_transitions():
            obj.states.auto_submit()

        super().save_model(request, obj, form, change)

        segments = []
        for segment_type in SegmentType.objects.all():
            segments += form.cleaned_data.get(segment_type.field_name, [])

        if segments:
            obj.segments.set(segments)

    show_in_index = True
    date_hierarchy = 'created'

    ordering = ('-created',)

    readonly_fields = [
        'created',
        'updated',
        'has_deleted_data',
        'valid',
        'transition_date',
        'stats_data',
        'review_status',
        'send_impact_reminder_message_link',
    ]

    office_fields = (
        'office_location',
    )

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

    registration_fields = None

    def get_registration_fields(self, request, obj):
        return self.registration_fields

    def get_inline_instances(self, request, obj=None):
        inlines = super(ActivityChildAdmin, self).get_inline_instances(request, obj)
        if InitiativePlatformSettings.objects.get().enable_impact:
            impact_goal_inline = ImpactGoalInline(self.model, self.admin_site)
            inlines.append(impact_goal_inline)

        if not obj or (
            obj.team_activity != Activity.TeamActivityChoices.teams or
            obj._initial_values['team_activity'] != Activity.TeamActivityChoices.teams
        ):
            inlines = [
                inline for inline in inlines if not isinstance(inline, TeamInline)
            ]

        return inlines

    def get_list_filter(self, request):
        filters = list(self.list_filter)
        settings = InitiativePlatformSettings.objects.get()
        from bluebottle.geo.models import Location
        if Location.objects.count():
            filters = filters + [('office_location', admin.RelatedOnlyFieldListFilter)]
            if settings.enable_office_regions and not request.user.region_manager:
                filters = filters + [
                    'office_location__subregion',
                    'office_location__subregion__region'
                ]

        if settings.team_activities:
            filters = filters + ['team_activity']

        return filters

    def get_list_display(self, request):
        fields = list(self.list_display)
        from bluebottle.geo.models import Location
        if Location.objects.count():
            fields = fields + ['office_location']
        return fields

    def get_status_fields(self, request, obj):
        fields = self.status_fields
        if obj and obj.status in ('draft', 'submitted', 'needs_work'):
            fields = ('valid',) + fields

        return fields

    def get_detail_fields(self, request, obj):
        settings = InitiativePlatformSettings.objects.get()
        detail_fields = self.detail_fields
        if isinstance(detail_fields, list):
            detail_fields = tuple(detail_fields)
        if Location.objects.exists() and not settings.enable_office_restrictions:
            detail_fields += ('office_location',)
        return detail_fields

    list_display = [
        '__str__', 'initiative_link', 'state_name',
    ]

    def initiative_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:initiatives_initiative_change', args=(obj.initiative.id,)),
            obj.initiative
        )

    initiative_link.short_description = _('Initiative')

    def get_fieldsets(self, request, obj=None):
        settings = InitiativePlatformSettings.objects.get()
        fieldsets = [
            (_("Management"), {"fields": self.get_status_fields(request, obj)}),
            (_("Information"), {"fields": self.get_detail_fields(request, obj)}),
        ]
        if self.get_registration_fields(request, obj):
            fieldsets.append(
                (
                    _("Participation"),
                    {"fields": self.get_registration_fields(request, obj)},
                )
            )

        if Location.objects.count():
            if settings.enable_office_restrictions:
                if 'office_restriction' not in self.office_fields:
                    self.office_fields += (
                        'office_restriction',
                    )
            fieldsets.append((
                _('Office'), {'fields': self.office_fields}
            ))

        if SegmentType.objects.count():
            fieldsets.append((
                _('Segments'), {
                    'fields': [
                        segment_type.field_name
                        for segment_type in SegmentType.objects.all()
                    ]
                }
            ))

        if request.user.is_superuser:
            fieldsets.append(
                (_('Super admin'), {'fields': (
                    'force_status',
                )})
            )

        return fieldsets

    def stats_data(self, obj):
        template = loader.get_template(
            'admin/activity_stats.html'
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

        template = loader.get_template(
            'admin/validation_steps.html'
        )
        return template.render({'errors': errors})

    valid.short_description = _('Validation')

    def get_urls(self):
        urls = super(ActivityChildAdmin, self).get_urls()

        extra_urls = [
            url(
                r'^(?P<pk>\d+)/bulk_add/$',
                self.admin_site.admin_view(self.bulk_add_participants),
                name='{}_{}_bulk_add'.format(
                    self.model._meta.app_label,
                    self.model._meta.model_name
                ),
            ),
            url(
                r'^send-impact-reminder-message/(?P<pk>\d+)/$',
                self.admin_site.admin_view(self.send_impact_reminder_message),
                name='{}_{}_send_impact_reminder_message'.format(
                    self.model._meta.app_label,
                    self.model._meta.model_name
                ),
            )
        ]
        return extra_urls + urls

    def bulk_add_participants(self, request, pk, *args, **kwargs):
        activity = self.model.objects.get(pk=pk)
        route = 'admin:{}_{}_change'.format(
            self.model._meta.app_label,
            self.model._meta.model_name
        )

        activity_detail = reverse(route, args=(pk,))

        if not request.user.is_superuser:
            return HttpResponseRedirect(activity_detail + '#/tab/inline_0/')

        if request.method == "POST":
            form = ActivityBulkAddForm(data=request.POST, activity=activity)
            if form.is_valid():
                data = form.cleaned_data
                emails = re.split(r'[,;\n]', data['emails'])
                send_messages = data['send_messages']
                result = bulk_add_participants(activity, emails, send_messages)
                if result['added']:
                    messages.add_message(
                        request,
                        messages.INFO,
                        ngettext(
                            '{count} participant was added.',
                            '{count} participants were added.',
                            result['added']
                        ).format(count=result['added'])
                    )
                if result['created']:
                    messages.add_message(
                        request,
                        messages.INFO,
                        ngettext(
                            '{count} user created and added as a participant.',
                            '{count} users created and added as a participant.',
                            result['added']
                        ).format(count=result['created'])
                    )

                if result['existing']:
                    messages.add_message(
                        request,
                        messages.INFO,
                        ngettext(
                            '{count} participant already joined.',
                            '{count} participants already joined.',
                            result['existing']
                        ).format(count=result['existing'])
                    )

                if result['failed']:
                    messages.add_message(
                        request,
                        messages.WARNING,
                        ngettext(
                            '{count} participant could not be added. Please check if the email address is correct.',
                            '{count} participants could not be added. Please check if the email addresses are correct.',
                            result['failed']
                        ).format(count=result['failed'])
                    )
            return HttpResponseRedirect(activity_detail + '#/tab/inline_0/')

        context = {
            'opts': self.model._meta,
            'activity': activity,
            'form': ActivityBulkAddForm(activity=activity)
        }
        return TemplateResponse(
            request, 'admin/activities/bulk_add.html', context
        )

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

        return HttpResponseRedirect(reverse('admin:activities_activity_change', args=(activity.id,)))

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


@admin.register(Activity)
class ActivityAdmin(PolymorphicParentModelAdmin, RegionManagerAdminMixin, StateMachineAdmin):
    base_model = Activity
    child_models = (
        Funding,
        DateActivity,
        Deed,
        CollectActivity,
        DeadlineActivity,
        PeriodicActivity,
        ScheduleActivity
    )
    date_hierarchy = 'transition_date'
    readonly_fields = ['link', 'review_status']
    list_filter = [PolymorphicChildModelFilter, StateMachineFilter, 'highlight', ]

    def lookup_allowed(self, key, value):
        if key in [
            'goals__type__id__exact',
            'office_location__id__exact',
            'office_location__subregion__id__exact',
            'office_location__subregion__region__id__exact',
        ]:
            return True
        return super(ActivityAdmin, self).lookup_allowed(key, value)

    def get_list_filter(self, request):
        settings = InitiativePlatformSettings.objects.get()
        filters = list(self.list_filter)
        from bluebottle.geo.models import Location
        if Location.objects.count():
            filters = filters + [('office_location', admin.RelatedOnlyFieldListFilter)]
            if settings.enable_office_regions and not request.user.region_manager:
                filters = filters + [
                    'office_location__subregion',
                    'office_location__subregion__region'
                ]

        if settings.team_activities:
            filters = filters + ['team_activity']
        return filters

    list_display = ['__str__', 'created', 'type', 'state_name',
                    'link', 'highlight']

    def location_link(self, obj):
        if not obj.office_location:
            return "-"
        url = reverse('admin:geo_location_change', args=(obj.office_location.id,))
        return format_html('<a href="{}">{}</a>', url, obj.office_location)

    location_link.short_description = _('office')

    def get_list_display(self, request):
        fields = list(self.list_display)
        from bluebottle.geo.models import Location
        if Location.objects.count():
            fields = fields + ['office_location']
        return fields

    search_fields = ('title', 'description',
                     'owner__first_name', 'owner__last_name')

    def link(self, obj):
        return format_html(u'<a href="{}" target="_blank">{}</a>', obj.get_absolute_url(), obj.title)

    link.short_description = _("Show on site")

    ordering = ('-created',)

    def type(self, obj):
        if obj.team_activity == 'teams':
            return _('Team activity')
        return obj.get_real_instance_class()._meta.verbose_name


class ActivityInlineChild(StackedPolymorphicInline.Child):
    ordering = ['-created']

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

    activity_link.short_description = _('Edit')


class ActivityAdminInline(StackedPolymorphicInline):
    model = Activity
    readonly_fields = ['title', 'created', 'owner']
    fields = readonly_fields
    extra = 0
    can_delete = False
    ordering = ['-created']

    class CollectActivityInline(ActivityInlineChild):
        readonly_fields = ['activity_link', 'start', 'end', 'state_name']
        fields = readonly_fields
        model = CollectActivity

    class DeedInline(ActivityInlineChild):
        readonly_fields = ['activity_link', 'start', 'end', 'state_name']
        fields = readonly_fields
        model = Deed

    class FundingInline(ActivityInlineChild):
        readonly_fields = ['activity_link', 'target', 'deadline', 'state_name']
        fields = readonly_fields
        model = Funding

    class DateInline(ActivityInlineChild):
        readonly_fields = ['activity_link', 'start', 'state_name']

        fields = readonly_fields
        model = DateActivity

    class DeadlineInline(ActivityInlineChild):
        readonly_fields = ['activity_link', 'start', 'deadline', 'state_name']
        fields = readonly_fields
        model = DeadlineActivity

    class PeriodicInline(ActivityInlineChild):
        readonly_fields = ["activity_link", "start", "deadline", "state_name"]
        fields = readonly_fields
        model = PeriodicActivity

    class ScheduleInline(ActivityInlineChild):
        readonly_fields = ["activity_link", "start", "deadline", "state_name"]
        fields = readonly_fields
        model = ScheduleActivity

    child_inlines = (
        FundingInline,
        DeadlineInline,
        PeriodicInline,
        ScheduleInline,
        DateInline,
        DeedInline,
        CollectActivityInline
    )

    pagination_key = 'page'
    template = 'admin/activities_paginated.html'

    per_page = 10

    def get_formset(self, request, obj=None, **kwargs):
        formset_class = super().get_formset(request, obj, **kwargs)

        class PaginationFormSet(PaginationFormSetBase, formset_class):
            pagination_key = self.pagination_key

        PaginationFormSet.request = request
        PaginationFormSet.per_page = self.per_page
        return PaginationFormSet


class BaseContributionInline(admin.TabularInline):
    model = Contribution
    extra = 0
    readonly_fields = ('status_label', 'start',)
    fields = readonly_fields + ('value',)

    def has_change_permission(self, request, obj=None):
        return False

    def status_label(self, obj):
        return not obj.states.current_state.name
