from collections import OrderedDict
import logging
from decimal import InvalidOperation

from bluebottle.tasks.models import Skill
from django import forms
from django.db import connection
from django.conf.urls import url
from django.contrib import admin, messages
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.db.models import Count, Sum
from django.utils.html import format_html
from django.http.response import HttpResponseRedirect, HttpResponseForbidden
from django.utils.translation import ugettext_lazy as _

from daterange_filter.filter import DateRangeFilter
from django_summernote.widgets import SummernoteWidget
from sorl.thumbnail.admin import AdminImageMixin

from bluebottle.bb_projects.models import ProjectTheme, ProjectPhase
from bluebottle.payouts_dorado.adapters import (
    DoradoPayoutAdapter, PayoutValidationError, PayoutCreationError
)
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
from .tasks import refund_project

logger = logging.getLogger(__name__)


def mark_as(slug, queryset):
    try:
        status = ProjectPhase.objects.get(slug=slug)
    except ProjectPhase.DoesNotExist:
        return

    # NOTE: To trigger the post save signals, resist using bulk updates
    # REF: https://docs.djangoproject.com/en/1.10/ref/models/querysets/#update
    projects = Project.objects.filter(pk__in=queryset.values_list('pk', flat=True))
    for project in projects:
        project.status = status
        project.save()


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
            return queryset.filter(theme=self.value())
        else:
            return queryset


class ProjectSkillFilter(admin.SimpleListFilter):
    title = _('Task skills')
    parameter_name = 'skill'

    def lookups(self, request, model_admin):
        skills = Skill.objects.filter(disabled=False)
        lookups = [(skill.id, _(skill.name)) for skill in skills]
        return [('any', _('Any expertise based skill'))] + lookups

    def queryset(self, request, queryset):
        if self.value():
            if self.value() == 'any':
                return queryset.filter(task__skill__isnull=False, task__skill__expertise=True)
            else:
                return queryset.filter(task__skill=self.value())
        else:
            return queryset


class ProjectReviewerFilter(admin.SimpleListFilter):
    title = _('Reviewer')
    parameter_name = 'reviewer'

    def lookups(self, request, model_admin):
        return ((True, _('My projects')), )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                reviewer=request.user
            )
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
            return format_html(
                u"<a href='{}'>{}</a>",
                str(url), 'Download'
            )
        return '(None)'


class RewardInlineAdmin(admin.TabularInline):
    model = Reward
    readonly_fields = ('count',)
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


class ReviewerWidget(admin.widgets.ForeignKeyRawIdWidget):
    def url_parameters(self):
        parameters = super(ReviewerWidget, self).url_parameters()
        parameters['is_staff'] = True
        return parameters


class ProjectAdminForm(forms.ModelForm):
    class Meta:
        widgets = {
            'currencies': forms.CheckboxSelectMultiple,
            'story': SummernoteWidget()
        }

    theme = forms.ModelChoiceField(queryset=ProjectTheme.objects.all().filter(disabled=False))

    def __init__(self, *args, **kwargs):
        super(ProjectAdminForm, self).__init__(*args, **kwargs)
        self.fields['currencies'].required = False

        self.fields['reviewer'].widget = ReviewerWidget(
            rel=Project._meta.get_field('reviewer').rel,
            admin_site=admin.sites.site
        )


class ProjectAdmin(AdminImageMixin, ImprovedModelForm):
    form = ProjectAdminForm
    date_hierarchy = 'created'
    ordering = ('-created',)
    save_on_top = True
    search_fields = ('title', 'owner__first_name', 'owner__last_name', 'organization__name')
    raw_id_fields = ('owner', 'reviewer', 'task_manager', 'promoter', 'organization',)
    prepopulated_fields = {'slug': ('title',)}

    inlines = (ProjectBudgetLineInline, RewardInlineAdmin, TaskAdminInline, ProjectDocumentInline,
               ProjectPhaseLogInline)

    list_filter = ('country__subregion__region', )

    export_fields = [
        ('title', 'title'),
        ('owner', 'owner'),
        ('owner__remote_id', 'remote id'),
        ('reviewer', 'reviewer'),
        ('task_manager', 'task_manager'),
        ('promoter', 'promoter'),
        ('created', 'created'),
        ('status', 'status'),
        ('payout_status', 'payout status'),
        ('theme', 'theme'),
        ('location__group', 'region'),
        ('country', 'country'),
        ('location', 'location'),
        ('deadline', 'deadline'),
        ('date_submitted', 'date submitted'),
        ('campaign_started', 'campaign started'),
        ('campaign_ended', 'campaign ended'),
        ('campaign_funded', 'campaign funded'),
        ('campaign_paid_out', 'campaign paid out'),
        ('task_count', 'task count'),
        ('supporters', 'supporters'),
        ('time_spent', 'time spent'),
        ('amount_asked', 'amount asked'),
        ('amount_donated', 'amount donated'),
        ('organization__name', 'organization'),
        ('amount_extra', 'amount matched'),
        ('expertise_based', 'expertise based'),
    ]

    actions = [export_as_csv_action(fields=export_fields),
               mark_as_closed, mark_as_done_incomplete,
               mark_as_done_complete, mark_as_campaign,
               mark_as_voting_done, mark_as_voting,
               mark_as_plan_needs_work, mark_as_plan_submitted,
               mark_as_plan_new]

    # Fields
    def num_votes(self, obj):
        self.queryset(None)
        return obj.admin_vote_count

    num_votes.short_description = _('Vote Count')
    num_votes.admin_order_field = 'admin_vote_count'

    def get_title_display(self, obj):
        if len(obj.title) > 35:
            return format_html(
                u'<span title="{}">{} &hellip;</span>',
                obj.title, obj.title[:45]
            )
        return obj.title

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
        return format_html(
            u"<a href='{}'>{}</a>",
            str(url),
            object.first_name + ' ' + object.last_name
        )

    def vote_count(self, obj):
        return obj.vote_set.count()

    def donated_percentage(self, obj):
        try:
            percentage = "%.2f" % (100 * obj.amount_donated.amount / obj.amount_asked.amount)
            return "{0} %".format(percentage)
        except (AttributeError, InvalidOperation):
            return '-'

    def expertise_based(self, obj):
        return obj.expertise_based

    expertise_based.boolean = True

    def approve_payout(self, request, pk=None):
        project = Project.objects.get(pk=pk)
        if not request.user.has_perm('projects.approve_payout'):
            return HttpResponseForbidden('Missing permission: projects.approve_payout')
        elif project.payout_status != 'needs_approval':
            self.message_user(request, 'The payout does not have the status "needs approval"')
        else:
            adapter = DoradoPayoutAdapter(project)
            try:
                adapter.trigger_payout()
            except PayoutValidationError as e:
                errors = e.message['errors']
                if type(errors) == unicode:
                    self.message_user(
                        request,
                        'Account details: {}.'.format(errors),
                        level=messages.ERROR
                    )
                else:
                    for field, errors in errors.items():
                        for error in errors:
                            self.message_user(
                                request,
                                'Account details: {}, {}.'.format(field, error.lower()),
                                level=messages.ERROR
                            )
            except (PayoutCreationError, ImproperlyConfigured) as e:
                logger.warning(
                    'Error approving payout: {}'.format(e),
                    exc_info=1
                )

                self.message_user(
                    request,
                    'Failed to approve payout: {}'.format(e),
                    level=messages.ERROR
                )

        project_url = reverse('admin:projects_project_change', args=(project.id,))
        return HttpResponseRedirect(project_url)

    def refund(self, request, pk=None):
        project = Project.objects.get(pk=pk)

        if not request.user.has_perm('payments.refund_orderpayment') or not project.can_refund:
            return HttpResponseForbidden('Missing permission: payments.refund_orderpayment')

        refund_project.delay(connection.tenant, project)
        project_url = reverse('admin:projects_project_change', args=(project.id,))
        return HttpResponseRedirect(project_url)

    def amount_donated_i18n(self, obj):
        return obj.amount_donated

    amount_donated_i18n.short_description = _('Amount Donated')

    def amount_needed_i18n(self, obj):
        return obj.amount_needed

    amount_needed_i18n.short_description = _('Amount Needed')

    # Setup
    def get_readonly_fields(self, request, obj=None):
        fields = ['vote_count', 'amount_donated_i18n', 'amount_needed_i18n', 'popularity', 'payout_status']
        if obj and obj.payout_status and obj.payout_status != 'needs_approval':
            fields += ('status', )
        return fields

    def get_urls(self):
        urls = super(ProjectAdmin, self).get_urls()
        process_urls = [
            url(r'^approve_payout/(?P<pk>\d+)/$',
                self.approve_payout,
                name="projects_project_approve_payout"),
            url(r'^refund/(?P<pk>\d+)/$',
                self.refund,
                name="projects_project_refund"),
        ]
        return process_urls + urls

    def get_list_filter(self, request):
        filters = ['status', 'is_campaign', ProjectThemeFilter, ProjectSkillFilter,
                   ProjectReviewerFilter, 'project_type', ('deadline', DateRangeFilter), ]

        if request.user.has_perm('projects.approve_payout'):
            filters.insert(1, 'payout_status')

        # Only show Location column if there are any
        if Location.objects.count():
            filters += [LocationGroupFilter, LocationFilter]
        else:
            filters += ['country__subregion__region', ('country', admin.RelatedOnlyFieldListFilter), ]
        return filters

    def get_list_display(self, request):
        fields = ['get_title_display', 'get_owner_display', 'created', 'status', 'deadline', 'donated_percentage',
                  'amount_extra', 'expertise_based']

        if request.user.has_perm('projects.approve_payout'):
            fields.insert(4, 'payout_status')

        # Only show Location column if there are any
        if Location.objects.count():
            fields += ('location',)
        # Only show Vote_count column if there are any votes
        if Vote.objects.count():
            fields += ('vote_count',)
        return fields

    def get_list_editable(self, request):
        return ('is_campaign',)

    def get_actions(self, request):
        """Order the action in reverse (delete at the bottom)."""
        actions = super(ProjectAdmin, self).get_actions(request)
        return OrderedDict(reversed(actions.items()))

    def get_fieldsets(self, request, obj=None):
        main = {'fields': ['owner', 'reviewer', 'task_manager', 'promoter', 'organization', 'status', 'title', 'slug',
                           'project_type', 'is_campaign', 'celebrate_results']}

        if request.user.has_perm('projects.approve_payout'):
            main['fields'].insert(3, 'payout_status')

        return (
            (_('Main'), main),

            (_('Story'), {'fields': ('pitch', 'story', 'reach')}),

            (_('Details'), {'fields': ('language', 'theme', 'categories', 'image', 'video_url', 'country', 'latitude',
                                       'longitude', 'location', 'place')}),

            (_('Goal'), {'fields': ('amount_asked', 'amount_extra', 'amount_donated_i18n', 'amount_needed_i18n',
                                    'currencies', 'popularity', 'vote_count')}),

            (_('Dates'), {'fields': ('voting_deadline', 'deadline', 'date_submitted', 'campaign_started',
                                     'campaign_ended', 'campaign_funded', 'campaign_paid_out')}),

            (_('Bank details'), {'fields': ('account_holder_name',
                                            'account_holder_address',
                                            'account_holder_postal_code',
                                            'account_holder_city',
                                            'account_holder_country',
                                            'account_number',
                                            'account_details',
                                            'account_bank_country')})
        )

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


admin.site.register(Project, ProjectAdmin)


class ProjectPhaseAdmin(admin.ModelAdmin):

    list_display = ['__unicode__', 'name', 'slug']


admin.site.register(ProjectPhase, ProjectPhaseAdmin)
