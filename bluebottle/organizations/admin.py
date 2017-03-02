from django.contrib import admin

from bluebottle.organizations.models import Organization
from bluebottle.projects.models import Project
from bluebottle.utils.admin import export_as_csv_action


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

    list_display = ('name', 'website', 'phone_number', 'created')
    list_filter = (
        ('project__theme', admin.RelatedOnlyFieldListFilter),
        ('project__location', admin.RelatedOnlyFieldListFilter),
    )
    fields = ('name', 'email', 'phone_number', 'website')

    search_fields = ('name',)
    export_fields = [
        ('name', 'name'),
        ('website', 'website'),
        ('phone_number', 'phone_number'),
        ('created', 'created'),
    ]

    actions = (export_as_csv_action(fields=export_fields), )


admin.site.register(Organization, OrganizationAdmin)
