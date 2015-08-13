import logging

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.core.urlresolvers import reverse
from django.utils.html import escape

from sorl.thumbnail.admin import AdminImageMixin

from bluebottle.common.admin_utils import ImprovedModelForm
from bluebottle.geo.admin import LocationFilter
from bluebottle.geo.models import Location

from bluebottle.bb_projects.admin import ProjectDocumentInline
from bluebottle.bb_tasks.admin import TaskAdminInline
from bluebottle.utils.admin import export_as_csv_action
from bluebottle.votes.models import Vote
from bluebottle.bb_projects.models import ProjectTheme

from geoposition.widgets import GeopositionWidget


from .models import PartnerOrganization, ProjectBudgetLine, Project, ProjectPhaseLog

logger = logging.getLogger(__name__)


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


class PartnerOrganizationAdmin(AdminImageMixin, admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


admin.site.register(PartnerOrganization, PartnerOrganizationAdmin)


class ProjectBudgetLineInline(admin.TabularInline):
    model = ProjectBudgetLine
    extra = 0


class ProjectPhaseLogInline(admin.TabularInline):
    model = ProjectPhaseLog
    can_delete = False

    def has_add_permission(self, request):
        return False

    readonly_fields = ('status', 'start')
    fields = readonly_fields


class ProjectAdminForm(forms.ModelForm):
    theme = forms.ModelChoiceField(queryset=ProjectTheme.objects.all().filter(disabled=False))


class ProjectAdmin(AdminImageMixin, ImprovedModelForm):
    form = ProjectAdminForm
    date_hierarchy = 'created'
    ordering = ('-created',)
    save_on_top = True

    search_fields = ('title', 'owner__first_name', 'owner__last_name', 'organization__name')

    raw_id_fields = ('owner', 'organization',)

    prepopulated_fields = {'slug': ('title',)}

    inlines = (ProjectBudgetLineInline, TaskAdminInline, ProjectDocumentInline, ProjectPhaseLogInline)

    def get_list_filter(self, request):
        filters = ('status', 'is_campaign', 'theme', 'country__subregion__region',
                'partner_organization', FundingFilter)

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

    readonly_fields = ('owner_link', 'organization_link', 'vote_count',
                       'amount_donated', 'amount_needed', 'popularity')

    export_fields = ['title', 'owner', 'created', 'status',
                     'deadline', 'amount_asked', 'amount_donated']

    actions = (export_as_csv_action(fields=export_fields), )

    fieldsets = (
        (_('Main'), {'fields': ('owner', 'owner_link',
                                'organization', 'organization_link',
                                'partner_organization',
                                'status', 'title', 'slug', 'is_campaign')}),

        (_('Story'), {'fields': ('pitch', 'story', 'reach')}),

        (_('Details'), {'fields': ('language', 'theme', 'image',
                                   'video_url', 'country',
                                   'latitude', 'longitude',
                                   'location', 'place', 'tags')}),

        (_('Goal'), {'fields': ('amount_asked', 'amount_extra',
                                'amount_donated','amount_needed',
                                'popularity', 'vote_count')}),

        (_('Dates'), {'fields': ('deadline', 'date_submitted',
                                 'campaign_started', 'campaign_ended',
                                 'campaign_funded', 'voting_deadline')}),

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

    def owner_link(self, obj):
        object = obj.owner
        url = reverse('admin:%s_%s_change' % (
            object._meta.app_label, object._meta.module_name),
            args=[object.id])
        return "<a href='%s'>%s</a>" % (str(url),
                                        object.first_name + ' ' +
                                        object.last_name)

    owner_link.allow_tags = True

    def organization_link(self, obj):
        object = obj.organization
        url = reverse('admin:%s_%s_change' % (
            object._meta.app_label, object._meta.module_name),
            args=[object.id])
        return "<a href='%s'>%s</a>" % (str(url), object.name)

    organization_link.allow_tags = True

    def donated_percentage(self, obj):
        if not obj.amount_asked:
            return "-"
        percentage = "%.2f" % (100 * obj.amount_donated / obj.amount_asked)
        return "{0} %".format(percentage)

    def queryset(self, request):
        # Optimization: Select related fields that are used in admin specific display fields.
        queryset = super(ProjectAdmin, self).queryset(request)
        return queryset.select_related('projectpitch', 'projectplan', 'projectcampaign', 'owner',
                                       'organization')

    def get_title_display(self, obj):
        if len(obj.title) > 50:
            return u'<span title="{title}">{short_title} [...]</span>'.format(title=escape(obj.title),
                                                                              short_title=obj.title[:45])
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
        url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label, object._meta.module_name), args=[object.id])
        return "<a href='{0}'>{1}</a>".format(str(url), object.first_name + ' ' + object.last_name)

    project_owner.allow_tags = True

admin.site.register(Project, ProjectAdmin)
