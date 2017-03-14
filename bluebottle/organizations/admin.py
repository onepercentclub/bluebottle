from django.contrib import admin, messages
from django.core.urlresolvers import reverse
from django.template.response import TemplateResponse
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext as _

from bluebottle.organizations.models import (Organization, OrganizationMember,
                                             OrganizationContact)
from bluebottle.projects.models import Project


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
    readonly_fields = ('title', 'owner', 'status')
    fields = ('title', 'owner', 'status')
    extra = 0

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class OrganizationMemberInline(admin.StackedInline):
    model = OrganizationMember
    raw_id_fields = ('user',)


class OrganizationContactInline(admin.StackedInline):
    model = OrganizationContact
    raw_id_fields = ('owner',)


class OrganizationAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    inlines = (OrganizationMemberInline, OrganizationContactInline,)

    list_display = ('name', 'created')

    search_fields = ('name',)


class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'function')
    list_filter = ('function',)
    raw_id_fields = ('user',)
    search_fields = ('user__first_name', 'user__last_name', 'user__username')


admin.site.register(OrganizationMember, OrganizationMemberAdmin)
admin.site.register(Organization, OrganizationAdmin)
