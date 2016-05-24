from collections import OrderedDict
import logging

from django import forms
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _

from sorl.thumbnail.admin import AdminImageMixin

from bluebottle.bb_projects.models import ProjectTheme, ProjectPhase
from bluebottle.rewards.models import Reward
from bluebottle.tasks.admin import TaskAdminInline
from bluebottle.common.admin_utils import ImprovedModelForm
from bluebottle.geo.admin import LocationFilter
from bluebottle.geo.models import Location
from bluebottle.utils.admin import export_as_csv_action
from bluebottle.votes.models import Vote

from .forms import ProjectDocumentForm
from .models import (ProjectBudgetLine, Project,
                     ProjectDocument, ProjectPhaseLog)

logger = logging.getLogger(__name__)


class ProjectThemeAdmin(admin.ModelAdmin):
    list_display = admin.ModelAdmin.list_display + ('slug', 'disabled',)


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
            ('yes', _('Funding')),
            ('no', _('Not funding')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(amount_asked__gt=0)
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

    list_filter = ('country__subregion__region',)

    def get_list_filter(self, request):
        filters = ('status', 'is_campaign', ProjectThemeFilter,
                   'country__subregion__region',
                   FundingFilter)

        # Only show Location column if there are any
        if Location.objects.count():
            filters +=  (LocationFilter, )
        return filters

    def get_list_display(self, request):
        fields = ('get_title_display', 'get_owner_display', 'created',
                  'status', 'is_campaign', 'deadline', 'donated_percentage')
        # Only show Location column if there are any
        if Location.objects.count():
            fields +=  ('location', )
        # Only show Vote_count column if there are any votes
        if Vote.objects.count():
            fields +=  ('vote_count', )
        return fields

    def get_list_editable(self, request):
        return ('is_campaign', )

    readonly_fields = ('vote_count', 'amount_donated',
                       'amount_needed', 'popularity')

    export_fields = ['title', 'owner', 'created', 'status',
                     'deadline', 'amount_asked', 'amount_donated']

    actions = (export_as_csv_action(fields=export_fields), )

    def get_actions(self, request):
        """Order the action in reverse (delete at the bottom)."""
        actions = super(ProjectAdmin, self).get_actions(request)
        return OrderedDict(reversed(actions.items()))

    fieldsets = (
        (_('Main'), {'fields': ('owner', 'organization',
                                'status', 'title', 'slug', 'project_type',
                                'is_campaign')}),

        (_('Story'), {'fields': ('pitch', 'story', 'reach')}),

        (_('Details'), {'fields': ('language', 'theme', 'categories', 'image',
                                   'video_url', 'country',
                                   'latitude', 'longitude',
                                   'location', 'place', 'tags')}),

        (_('Goal'), {'fields': ('amount_asked', 'amount_extra',
                                'amount_donated', 'amount_needed',
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
        if not obj.amount_asked:
            return "-"
        percentage = "%.2f" % (100 * obj.amount_donated / obj.amount_asked)
        return "{0} %".format(percentage)

    def queryset(self, request):
        # Optimization: Select related fields that are used in admin specific
        # display fields.
        queryset = super(ProjectAdmin, self).queryset(request)
        queryset = queryset.select_related(
            'projectpitch', 'projectplan', 'projectcampaign', 'owner',
            'organization'
        ).extra(
            {'admin_vote_count': 'SELECT COUNT(*) from votes_vote where "votes_vote"."project_id" = "projects_project"."id"'}
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
