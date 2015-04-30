from django.contrib import admin

from bluebottle.utils.model_dispatcher import get_organization_model, get_organizationmember_model

ORGANIZATION_MODEL = get_organization_model()
MEMBER_MODEL = get_organizationmember_model()


class OrganizationMemberInline(admin.StackedInline):
    model = MEMBER_MODEL
    raw_id_fields = ('user', )
    extra = 0


class OrganizationAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    inlines = (OrganizationMemberInline, )

    list_display = ('name', 'created')

    search_fields = ('name',)

admin.site.register(ORGANIZATION_MODEL, OrganizationAdmin)


class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'function')
    list_filter = ('function',)
    raw_id_fields = ('user', )
    search_fields = ('user__first_name', 'user__last_name', 'user__username')

admin.site.register(MEMBER_MODEL, OrganizationMemberAdmin)
