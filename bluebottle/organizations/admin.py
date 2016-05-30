from django.contrib import admin

from bluebottle.organizations.models import OrganizationMember, Organization


class OrganizationMemberInline(admin.StackedInline):
    model = OrganizationMember
    raw_id_fields = ('user',)
    extra = 0


class OrganizationAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    inlines = (OrganizationMemberInline,)

    list_display = ('name', 'created')

    search_fields = ('name',)


admin.site.register(Organization, OrganizationAdmin)


class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'function')
    list_filter = ('function',)
    raw_id_fields = ('user',)
    search_fields = ('user__first_name', 'user__last_name', 'user__username')


admin.site.register(OrganizationMember, OrganizationMemberAdmin)
