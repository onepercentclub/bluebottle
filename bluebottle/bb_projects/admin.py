from django import forms
from bluebottle.common.admin_utils import ImprovedModelForm
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import escape
from django.utils.text import Truncator
from django.utils.translation import ugettext_lazy as _

from sorl.thumbnail.admin import AdminImageMixin

from bluebottle.utils.utils import get_project_model, get_project_phaselog_model
from .models import ProjectPhase, ProjectTheme


PROJECT_MODEL = get_project_model()
PROJECT_PHASELOG_MODEL = get_project_phaselog_model()

class ProjectThemeAdmin(admin.ModelAdmin):
    model = ProjectTheme
    prepopulated_fields = {'slug': ('name', 'name_nl')}

admin.site.register(ProjectTheme, ProjectThemeAdmin)


class ProjectPhaseLogInline(admin.TabularInline):
    model = PROJECT_PHASELOG_MODEL
    ordering = ('-start',)
    readonly_fields = ('status', 'start',)
    extra = 0


class BaseProjectAdmin(AdminImageMixin, ImprovedModelForm):
    inlines = [ProjectPhaseLogInline, ]
    date_hierarchy = 'created'
    ordering = ('-created',)
    save_on_top = True

    actions = ('set_failed', 'toggle_campaign')

    list_filter = ('status', )
    list_display = ('get_title_display', 'get_owner_display', 'created', 'status')

    search_fields = ('title', 'owner__first_name', 'owner__last_name', 'organization__name')

    raw_id_fields = ('owner', 'organization',)

    prepopulated_fields = {'slug': ('title',)}

    readonly_fields = ('amount_donated', 'amount_needed', 'popularity')

    def queryset(self, request):
        # Optimization: Select related fields that are used in admin specific display fields.
        queryset = super(BaseProjectAdmin, self).queryset(request)
        return queryset.select_related('projectpitch', 'projectplan', 'projectcampaign', 'owner',
                                       'organization')

    def get_title_display(self, obj):
        if len(obj.title) > 50:
            return u'<span title="{title}">{short_title} [...]</span>'.format(title=escape(obj.title),
                                                                              short_title=obj.title[:45])
        return obj.title

    get_title_display.allow_tags = True
    get_title_display.admin_order_field = 'title'
    get_title_display.short_description = _('title')

    def get_owner_display(self, obj):
        owner_name = obj.owner.get_full_name()
        if owner_name:
            owner_name = u' ({name})'.format(name=owner_name)
        return u'{email}{name}'.format(name=owner_name, email=obj.owner.email)

    get_owner_display.admin_order_field = 'owner__last_name'
    get_owner_display.short_description = _('owner')

    def project_owner(self, obj):
        object = obj.owner
        url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label, object._meta.module_name), args=[object.id])
        return "<a href='{0}'>{1}</a>".format(str(url), object.first_name + ' ' + object.last_name)

    project_owner.allow_tags = True

# if you want to display more fields, unregister the model first, define a new admin class
# (possibly inheriting from BaseProjectAdmin), and then re-register it
admin.site.register(PROJECT_MODEL, BaseProjectAdmin)


class ProjectPhaseAdmin(admin.ModelAdmin):
    model = ProjectPhase
    ordering = ['sequence']
    list_editable = ['active', 'editable', 'viewable', 'owner_editable']
    list_filter = ['active', ]
    list_display_links = ['name']
    list_display = ['sequence', 'name', 'active', 'editable', 'viewable', 'owner_editable']

admin.site.register(ProjectPhase, ProjectPhaseAdmin)
