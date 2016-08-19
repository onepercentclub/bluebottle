from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from bluebottle.common.admin_utils import ImprovedModelForm
from bluebottle.utils.admin import export_as_csv_action
from bluebottle.votes.models import Vote


class ProjectFilter(admin.SimpleListFilter):
    title = _('Project')
    parameter_name = 'project'

    def lookups(self, request, model_admin):
        projects = [obj.project for obj in model_admin.model.objects.order_by(
            'project__title').distinct('project__title').all()]
        return [(project.id, project.title) for project in projects]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(project__id__exact=self.value())
        else:
            return queryset


class VoteAdmin(ImprovedModelForm, admin.ModelAdmin):

    raw_id_fields = ('voter', 'project')
    list_display = ('email', 'first_name', 'last_name', 'project',
                    'created', 'ip_address')

    list_filter = ('created', ProjectFilter,)

    def get_queryset(self, request):
        return super(VoteAdmin, self).get_queryset(request).select_related('voter', 'project')

    def email(self, obj):
        return obj.voter.email

    email.admin_order_field = 'voter__email'

    def first_name(self, obj):
        return obj.voter.first_name

    first_name.admin_order_field = 'voter__first_name'

    def last_name(self, obj):
        return obj.voter.last_name

    last_name.admin_order_field = 'voter__last_name'

    export_fields = [('project', 'project'),
                     ('created', 'created'),
                     ('ip_address', 'ip address'),
                     ('voter', 'voter'),
                     ('voter__first_name', 'first name'),
                     ('voter__last_name', 'last name')]

    actions = (export_as_csv_action(fields=export_fields), )


admin.site.register(Vote, VoteAdmin)
