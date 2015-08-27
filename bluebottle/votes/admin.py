from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from bluebottle.common.admin_utils import ImprovedModelForm
from bluebottle.votes.models import Vote


class ProjectFilter(admin.SimpleListFilter):
    title = _('Project')
    parameter_name = 'project'

    def lookups(self, request, model_admin):
        projects = [obj.project for obj in model_admin.model.objects.order_by('project__title').distinct('project__title').all()]
        return [(project.id, project.title) for project in projects]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(project__id__exact=self.value())
        else:
            return queryset


class VoteAdmin(ImprovedModelForm, admin.ModelAdmin):
    raw_id_fields = ('voter', 'project')
    list_display = ('voter', 'project', 'created')
    list_filter = (ProjectFilter, )

admin.site.register(Vote, VoteAdmin)

