import logging

from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.core.urlresolvers import reverse

from sorl.thumbnail.admin import AdminImageMixin

from bluebottle.projects.models import ProjectBudgetLine, Project
from bluebottle.bb_projects.admin import BaseProjectAdmin, ProjectDocumentInline
from bluebottle.bb_tasks.admin import TaskAdminInline
from bluebottle.utils.admin import export_as_csv_action

from .models import PartnerOrganization

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


class ProjectAdmin(BaseProjectAdmin):
    inlines = (ProjectBudgetLineInline, TaskAdminInline, ProjectDocumentInline)

    list_filter = BaseProjectAdmin.list_filter + \
        ('is_campaign', 'theme', 'partner_organization', FundingFilter)
    list_display = BaseProjectAdmin.list_display + \
        ('is_campaign', 'deadline', 'donated_percentage')
    list_editable = ('is_campaign', )

    readonly_fields = ('owner_link', 'organization_link',
                       'amount_donated', 'amount_needed', 'popularity')

    export_fields = ['title', 'owner', 'created', 'status',
                     'deadline', 'amount_asked', 'amount_donated']
    actions = (export_as_csv_action(fields=export_fields), )

    fieldsets = (
        (_('Main'), {'fields': ('owner', 'organization', 'status', 'title',
                                'slug', 'pitch',
                                'theme', 'favorite', 'deadline', 'image',
                                'video_url',
                                'country', 'language', 'latitude', 'longitude',
                                'amount_asked', 'amount_extra',
                                'reach', 'is_campaign', 'skip_monthly',
                                'allow_overfunding', 'story',
                                'date_submitted', 'campaign_started',
                                'campaign_ended', 'campaign_funded', 'tags',
                                'amount_donated', 'amount_needed',
                                'popularity')}),
        (_('Bank details'), {'fields': ('account_holder_name',
                                        'account_holder_address',
                                        'account_holder_postal_code',
                                        'account_holder_city',
                                        'account_holder_country',
                                        'account_number',
                                        'account_bic',
                                        'account_bank_country')})
    )

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


# We wrapped this in a try because sometimes Project hasn't got registered
# before it hits this.
try:
    admin.site.unregister(Project)
except NotRegistered:
    pass
admin.site.register(Project, ProjectAdmin)
