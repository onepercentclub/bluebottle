from django.contrib import admin

from bluebottle.utils.model_dispatcher import get_organization_model, get_organizationdocument_model, get_organizationmember_model
from .forms import OrganizationDocumentForm

ORGANIZATION_MODEL = get_organization_model()
MEMBER_MODEL = get_organizationmember_model()
DOCUMENT_MODEL = get_organizationdocument_model()


class OrganizationDocumentInline(admin.StackedInline):
    model = DOCUMENT_MODEL
    form = OrganizationDocumentForm
    extra = 0
    raw_id_fields = ('author', )
    readonly_fields = ('download_url',)
    fields = readonly_fields + ('file', 'author')

    def download_url(self, obj):
        url = obj.document_url

        if url is not None:
            return "<a href='{0}'>{1}</a>".format(str(url), 'Download')
        return '(None)'
    download_url.allow_tags = True


class OrganizationMemberInline(admin.StackedInline):
    model = MEMBER_MODEL
    raw_id_fields = ('user', )
    extra = 0


class OrganizationAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    inlines = (OrganizationMemberInline, OrganizationDocumentInline)

    list_display = ('name', 'created', 'person')

    search_fields = ('name',)

admin.site.register(ORGANIZATION_MODEL, OrganizationAdmin)


class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'function')
    list_filter = ('function',)
    raw_id_fields = ('user', )
    search_fields = ('user__first_name', 'user__last_name', 'user__username')

admin.site.register(MEMBER_MODEL, OrganizationMemberAdmin)
