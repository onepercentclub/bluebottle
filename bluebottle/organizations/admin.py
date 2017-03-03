from django.contrib import admin, messages
from django.core.urlresolvers import reverse
from django.template.response import TemplateResponse
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext as _

from bluebottle.organizations.models import Organization
from bluebottle.projects.models import Project
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
    readonly_fields = ('title', 'owner', 'status')
    fields = ('title', 'owner', 'status')
    extra = 0

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class OrganizationAdmin(admin.ModelAdmin):
    inlines = (OrganizationProjectInline, )

    list_display = ('name', 'email', 'website', 'phone_number', 'created')
    list_filter = (
        ('projects__theme', admin.RelatedOnlyFieldListFilter),
        ('projects__location', admin.RelatedOnlyFieldListFilter),
    )
    fields = ('name', 'email', 'phone_number', 'website')

    search_fields = ('name',)
    export_fields = [
        ('name', 'name'),
        ('website', 'website'),
        ('phone_number', 'phone_number'),
        ('created', 'created'),
    ]

    actions = (export_as_csv_action(fields=export_fields), merge)


admin.site.register(Organization, OrganizationAdmin)
