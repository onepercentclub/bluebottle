from collections import OrderedDict
import logging
from decimal import InvalidOperation

from django import forms
from django.db.models import Count, Sum
from django.conf.urls import url
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _

from sorl.thumbnail.admin import AdminImageMixin

from bluebottle.bb_projects.models import ProjectTheme, ProjectPhase
from bluebottle.rewards.models import Reward
from bluebottle.tasks.admin import TaskAdminInline
from bluebottle.common.admin_utils import ImprovedModelForm
from bluebottle.geo.admin import LocationFilter, LocationGroupFilter
from bluebottle.geo.models import Location
from bluebottle.utils.admin import export_as_csv_action
from bluebottle.votes.models import Vote

from .forms import ProjectDocumentForm
from .models import (ProjectBudgetLine, Project,
                     ProjectDocument, ProjectPhaseLog)

logger = logging.getLogger(__name__)


def mark_as(slug, queryset):
    try:
        status = ProjectPhase.objects.get(slug=slug)
    except ProjectPhase.DoesNotExist:
        return

    Project.objects.filter(
        pk__in=queryset.values_list('pk', flat=True)
    ).update(
        status=status
    )


def mark_as_plan_new(modeladmin, request, queryset):
    mark_as('plan-new', queryset)
mark_as_plan_new.short_description = _("Mark selected projects as status Plan - Draft")


def mark_as_plan_submitted(modeladmin, request, queryset):
    mark_as('plan-submitted', queryset)
mark_as_plan_submitted.short_description = _("Mark selected projects as status Plan - Submitted")


def mark_as_plan_needs_work(modeladmin, request, queryset):
    mark_as('plan-needs-work', queryset)
mark_as_plan_needs_work.short_description = _("Mark selected projects as status Plan - Needs Work")


def mark_as_voting(modeladmin, request, queryset):
    mark_as('voting', queryset)
mark_as_voting.short_description = _("Mark selected projects as status Voting - Running")


def mark_as_voting_done(modeladmin, request, queryset):
    mark_as('voting-done', queryset)
mark_as_voting_done.short_description = _("Mark selected projects as status Voting - Done")


def mark_as_campaign(modeladmin, request, queryset):
    mark_as('campaign', queryset)
mark_as_campaign.short_description = _("Mark selected projects as status Project - Running")


def mark_as_done_complete(modeladmin, request, queryset):
    mark_as('done-complete', queryset)
mark_as_done_complete.short_description = _("Mark selected projects as status Project - Realised")


def mark_as_done_incomplete(modeladmin, request, queryset):
    mark_as('done-incomplete', queryset)
mark_as_done_incomplete.short_description = _("Mark selected projects as status Project - Done")


def mark_as_closed(modeladmin, request, queryset):
    mark_as('closed', queryset)
mark_as_closed.short_description = _("Mark selected projects as status Rejected / Canceled")


class ProjectThemeAdmin(admin.ModelAdmin):
    list_display = admin.ModelAdmin.list_display + ('slug', 'disabled',)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


admin.site.register(ProjectTheme, ProjectThemeAdmin)


class ProjectThemeFilter(admin.SimpleListFilter):
    title = _('Theme')
    parameter_name = 'theme'

    def lookups(self, request, model_admin):
        themes = [obj.theme for obj in
                  model_admin.model.objects.order_by('theme__name').distinct(
                      'theme__name').exclude(theme__isnull=True).all()]
        return [(theme.id, _(theme.name)) for theme in themes]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(theme__id__exact=self.value())
        else:
            return queryset


class ProjectDocumentInline(admin.StackedInline):
    model = ProjectDocument
    form = ProjectDocumentForm
    extra = 0
    raw_id_fields = ('author',)
    readonly_fields = ('download_url',)
    fields = readonly_fields + ('file', 'author')

    def download_url(self, obj):
        url = obj.document_url

        if url is not None:
            return "<a href='{0}'>{1}</a>".format(str(url), 'Download')
        return '(None)'

    download_url.allow_tags = True


class RewardInlineAdmin(admin.TabularInline):

    model = Reward
    readonly_fields = ('count', )
    extra = 0

    def count(self, obj):
        return obj.count


class ProjectPhaseLogInline(admin.TabularInline):
    model = ProjectPhaseLog
    can_delete = False
    ordering = ('-start',)
    extra = 0

    def has_add_permission(self, request):
        return False

    readonly_fields = ('status', 'start')
    fields = readonly_fields


class FundingFilter(admin.SimpleListFilter):
    title = _('Funding')
    parameter_name = 'funding'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('Crowdfunding')),
            ('no', _('Crowdsourcing')),
            ('both', _('Crowdfunding & crowdsourcing')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(amount_asked__gt=0)
        elif self.value() == 'no':
            from django.db.models import Q
            return queryset.filter(Q(amount_asked=None) | Q(amount_asked=0.00))
        return queryset


class ProjectBudgetLineInline(admin.TabularInline):
    model = ProjectBudgetLine
    extra = 0


class ProjectAdminForm(forms.ModelForm):
    theme = forms.ModelChoiceField(
        queryset=ProjectTheme.objects.all().filter(disabled=False))


class ProjectAdmin(AdminImageMixin, ImprovedModelForm):
    form = ProjectAdminForm
    date_hierarchy = 'created'
    ordering = ('-created',)
    save_on_top = True

    search_fields = ('title', 'owner__first_name', 'owner__last_name',
                     'organization__name')

    raw_id_fields = ('owner', 'organization',)

    prepopulated_fields = {'slug': ('title',)}

    inlines = (ProjectBudgetLineInline, RewardInlineAdmin, TaskAdminInline, ProjectDocumentInline,
               ProjectPhaseLogInline)

    readonly_fields = ('vote_count', 'amount_donated', 'payout_status',
                       'amount_needed', 'popularity')

    def get_urls(self):
        urls = super(ProjectAdmin, self).get_urls()
        process_urls = [
            url(r'^approve_payout/(?P<pk>\d+)/$',
                self.approve_payout,
                name="projects_project_approve_payout"),
        ]
        return process_urls + urls

    def approve_payouts(self, queryset):
        queryset.filter(payout_status='needs-approval').update(payout_status='approved')
    approve_payouts.short_description = _("Approve payouts for selected projects")

    def approve_payout(self, request, pk=None):
        project = Project.objects.get(pk=pk)
        if project.payout_status == 'needs_approval':
            project.payout_status = 'approved'
            project.save()
        project_url = reverse('admin:projects_project_change', args=(project.id,))
        response = HttpResponseRedirect(project_url)
        return response

    def get_list_filter(self, request):
        filters = ('status', 'is_campaign', ProjectThemeFilter, 'project_type')

        # Only show Location column if there are any
        if Location.objects.count():
            filters += (LocationGroupFilter, LocationFilter)
        else:
            filters += ('country__subregion__region', )
        return filters

    def get_list_display(self, request):
        fields = ('get_title_display', 'get_owner_display', 'created',
                  'status', 'payout_status',
                  'deadline', 'donated_percentage')
        # Only show Location column if there are any
        if Location.objects.count():
            fields += ('location', )
        # Only show Vote_count column if there are any votes
        if Vote.objects.count():
            fields += ('vote_count', )
        return fields

    def get_list_editable(self, request):
        return ('is_campaign', )

    export_fields = [
        ('title', 'title'),
        ('owner', 'owner'),
        ('owner__remote_id', 'remote id'),
        ('created', 'created'),
        ('status', 'status', 'payout_status'),
        ('theme', 'theme'),
        ('location__group', 'region'),
        ('location', 'location'),
        ('deadline', 'deadline'),
        ('date_submitted', 'date submitted'),
        ('campaign_started', 'campaign started'),
        ('campaign_ended', 'campaign ended'),
        ('campaign_funded', 'campaign funded'),
        ('task_count', 'task count'),
        ('supporters', 'supporters'),
        ('time_spent', 'time spent'),
        ('amount_asked', 'amount asked'),
        ('amount_donated', 'amount donated'),
    ]

    actions = [export_as_csv_action(fields=export_fields),
               mark_as_closed, mark_as_done_incomplete,
               mark_as_done_complete, mark_as_campaign,
               mark_as_voting_done, mark_as_voting,
               mark_as_plan_needs_work, mark_as_plan_submitted,
               mark_as_plan_new, approve_payouts]

    def get_actions(self, request):
        """Order the action in reverse (delete at the bottom)."""
        actions = super(ProjectAdmin, self).get_actions(request)
        return OrderedDict(reversed(actions.items()))

    fieldsets = (
        (_('Main'), {'fields': ('owner', 'organization',
                                'status', 'payout_status',
                                'title', 'slug', 'project_type',
                                'is_campaign', 'celebrate_results')}),

        (_('Story'), {'fields': ('pitch', 'story', 'reach')}),

        (_('Details'), {'fields': ('language', 'theme', 'categories', 'image',
                                   'video_url', 'country',
                                   'latitude', 'longitude',
                                   'location', 'place')}),

        (_('Goal'), {'fields': ('amount_asked', 'amount_extra',
                                'amount_donated', 'amount_needed',
                                'currencies',
                                'popularity', 'vote_count')}),

        (_('Dates'), {'fields': ('voting_deadline', 'deadline',
                                 'date_submitted', 'campaign_started',
                                 'campaign_ended', 'campaign_funded')}),

        (_('Bank details'), {'fields': ('account_holder_name',
                                        'account_holder_address',
                                        'account_holder_postal_code',
                                        'account_holder_city',
                                        'account_holder_country',
                                        'account_number',
                                        'account_bic',
                                        'account_bank_country')})
    )

    def vote_count(self, obj):
        return obj.vote_set.count()

    def donated_percentage(self, obj):
        try:
            percentage = "%.2f" % (100 * obj.amount_donated.amount / obj.amount_asked.amount)
            return "{0} %".format(percentage)
        except (AttributeError, InvalidOperation):
            return '-'

    def get_queryset(self, request):
        # Optimization: Select related fields that are used in admin specific
        # display fields.
        queryset = super(ProjectAdmin, self).get_queryset(request)
        queryset = queryset.select_related(
            'owner', 'organization'
        ).annotate(
            admin_vote_count=Count('vote', distinct=True),
            time_spent=Sum('task__members__time_spent')
        )

        return queryset

    def num_votes(self, obj):
        self.queryset(None)
        return obj.admin_vote_count

    num_votes.short_description = _('Vote Count')
    num_votes.admin_order_field = 'admin_vote_count'

    def get_title_display(self, obj):
        if len(obj.title) > 35:
            return u'<span title="{title}">{short_title} &hellip;</span>' \
                .format(title=escape(obj.title), short_title=obj.title[:45])
        return obj.title

    get_title_display.allow_tags = True
    get_title_display.admin_order_field = 'title'
    get_title_display.short_description = _('title')

    def get_owner_display(self, obj):
        owner_name = obj.owner.get_full_name()
        if owner_name:
            owner_name = u' ({name})'.format(name=owner_name)
        return u'{email}{name}'.format(name=owner_name, email=obj.owner.email)

    get_owner_display.admin_order_field = 'owner__last_name'
    get_owner_display.short_description = _('owner')

    def project_owner(self, obj):
        object = obj.owner
        url = reverse('admin:{0}_{1}_change'.format(
            object._meta.app_label, object._meta.model_name), args=[object.id])
        return "<a href='{0}'>{1}</a>".format(
            str(url), object.first_name + ' ' + object.last_name)

    project_owner.allow_tags = True


admin.site.register(Project, ProjectAdmin)

admin.site.register(ProjectPhase)
