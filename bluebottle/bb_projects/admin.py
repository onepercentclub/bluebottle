from django import forms
from bluebottle.common.admin_utils import ImprovedModelForm
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _

from sorl.thumbnail.admin import AdminImageMixin

from bluebottle.utils.model_dispatcher import get_project_model, get_project_phaselog_model, get_project_document_model

from .forms import ProjectDocumentForm

from .models import ProjectTheme


PROJECT_MODEL = get_project_model()
PROJECT_PHASELOG_MODEL = get_project_phaselog_model()
PROJECT_DOCUMENT_MODEL = get_project_document_model()

class ProjectThemeAdmin(admin.ModelAdmin):
    list_display = admin.ModelAdmin.list_display + \
        ('slug', 'disabled',)


admin.site.register(ProjectTheme, ProjectThemeAdmin)


class ProjectDocumentInline(admin.StackedInline):
    model = PROJECT_DOCUMENT_MODEL
    form = ProjectDocumentForm
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


class ProjectPhaseLogInline(admin.TabularInline):
    model = PROJECT_PHASELOG_MODEL
    ordering = ('-start',)
    readonly_fields = ('status', 'start',)
    extra = 0

