from django.contrib import admin, messages
from django.core.urlresolvers import reverse
from django.template.response import TemplateResponse
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.utils.html import format_html

from bluebottle.organizations.models import Organization, OrganizationContact
from bluebottle.projects.models import Project
from bluebottle.members.models import Member
from bluebottle.utils.admin import export_as_csv_action


def merge(modeladmin, request, queryset):
    if len(queryset) < 2:
        messages.add_message(request, messages.WARNING, _('Select at least 2 organizations to merge'))

        return HttpResponseRedirect(
            reverse('admin:organizations_organization_changelist')
        )
    if 'master' in request.POST:
        master = queryset.get(pk=request.POST['master'])
        master.merge(queryset.exclude(pk=master.pk))
        return HttpResponseRedirect(
            reverse('admin:organizations_organization_changelist')
        )
    else:
        return TemplateResponse(
            request,
            'admin/merge_preview.html',
            {
                'organizations': queryset,
                'current_app': modeladmin.admin_site.name,
                'title': _('Merge organizations'),
                'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME
            }
        )


merge.short_description = _('Merge Organizations')


class OrganizationProjectInline(admin.TabularInline):
    model = Project
    readonly_fields = ('project_url', 'owner', 'status')
    fields = ('project_url', 'owner', 'status')
    extra = 0

    def project_url(self, obj):
        url = reverse('admin:{0}_{1}_change'.format(obj._meta.app_label,
                                                    obj._meta.model_name),
                      args=[obj.id])
        return format_html(u"<a href='{}'>{}</a>", str(url), obj.title)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class OrganizationContactInline(admin.TabularInline):
    model = OrganizationContact
    verbose_name = "Contact"
    verbose_name_plural = "Contacts"
    readonly_fields = ('name', 'email', 'phone', 'creator')
    fields = ('name', 'email', 'phone', 'creator')

    def creator(self, obj):
        owner = obj.owner
        url = reverse('admin:{0}_{1}_change'.format(owner._meta.app_label,
                                                    owner._meta.model_name),
                      args=[owner.id])
        return format_html(u"<a href='{}'>{} {}</a>", str(url), owner.first_name, owner.last_name)

    creator.short_description = _('Creator')

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class PartnerOrganizationMembersInline(admin.TabularInline):
    model = Member
    verbose_name = "Partner Organization Member"
    verbose_name_plural = "Partner Organization Members"
    readonly_fields = ('member', 'phone_number', 'date_joined')
    fields = ('member', 'email', 'phone_number', 'date_joined')

    def member(self, obj):
        url = reverse('admin:{0}_{1}_change'.format(obj._meta.app_label, obj._meta.model_name), args=[obj.id])
        return format_html(u"<a href='{}'>{}</a>", str(url), obj.full_name)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class OrganizationAdmin(admin.ModelAdmin):
    inlines = (OrganizationProjectInline, OrganizationContactInline, PartnerOrganizationMembersInline)

    list_display = ('name', 'email', 'website', 'phone_number', 'created')
    list_filter = (
        ('projects__theme', admin.RelatedOnlyFieldListFilter),
        ('projects__location', admin.RelatedOnlyFieldListFilter),
    )
    fields = ('name', 'email', 'phone_number', 'website', 'description', 'logo')
    search_fields = ('name',)
    export_fields = [
        ('name', 'name'),
        ('website', 'website'),
        ('phone_number', 'phone_number'),
        ('created', 'created'),
    ]

    def get_inline_instances(self, request, obj=None):
        """ Override get_inline_instances so that add form do not show inlines """
        if not obj:
            return []
        return super(OrganizationAdmin, self).get_inline_instances(request, obj)

    actions = (export_as_csv_action(fields=export_fields), merge)


admin.site.register(Organization, OrganizationAdmin)
