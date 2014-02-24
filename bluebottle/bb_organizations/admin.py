from django.contrib import admin

from . import get_organization_model
from .forms import OrganizationDocumentForm
from .models import OrganizationDocument, OrganizationMember


ORGANIZATION_MODEL = get_organization_model()


class OrganizationDocumentInline(admin.StackedInline):
    model = OrganizationDocument
    form = OrganizationDocumentForm
    extra = 0
    raw_id_fields = ('author', )
    readonly_fields = ('download_url',)
    fields = readonly_fields + ('file', 'author')

    def download_url(self, obj):
        return "<a href='{0}'>{1}</a>".format(str(obj.document_url), 'Download')
    download_url.allow_tags = True


class OrganizationMemberInline(admin.StackedInline):
    model = OrganizationMember
    raw_id_fields = ('user', )
    extra = 0


class OrganizationAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    inlines = (OrganizationMemberInline, OrganizationDocumentInline)

    search_fields = ('name',)

    exclude = ('created', 'updated', 'deleted', 'tags')

admin.site.register(ORGANIZATION_MODEL, OrganizationAdmin)


class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'function', 'members')
    list_filter = ('function',)
    raw_id_fields = ('user', )
    search_fields = ('user__first_name', 'user__last_name', 'user__username')

admin.site.register(OrganizationMember, OrganizationMemberAdmin)
