from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _


from babel.numbers import format_currency
from sorl.thumbnail.admin import AdminImageMixin
import logging

from .models import Project


logger = logging.getLogger(__name__)


class ProjectAdmin(AdminImageMixin, admin.ModelAdmin):
    date_hierarchy = 'created'
    ordering = ('-created',)
    save_on_top = True
    actions = ('set_failed', 'toggle_campaign')

    list_filter = ('phase', )
    list_display = ('get_title_display', 'get_owner_display', 'created')

    search_fields = ('title', 'owner__first_name', 'owner__last_name', 'partner_organization__name')

    raw_id_fields = ('owner',)

    fields = ('owner', 'phase', 'title', 'pitch', 'image','description', 'reach',
              'latitude', 'longitude', 'country', 'video_url', 'money_needed', 'tags')

    def queryset(self, request):
        # Optimization: Select related fields that are used in admin specific display fields.
        queryset = super(ProjectAdmin, self).queryset(request)
        return queryset.select_related('projectpitch', 'projectplan', 'projectcampaign', 'owner',
                                       'partner_organization')

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

    def project_organization(self, obj):
        object = obj.projectplan.organization
        url = reverse('admin:%s_%s_change' % (object._meta.app_label, object._meta.module_name), args=[object.id])
        return "<a href='%s'>%s</a>" % (str(url), object.name)

    project_organization.allow_tags = True

    def project_owner(self, obj):
        object = obj.owner
        url = reverse('admin:%s_%s_change' % (object._meta.app_label, object._meta.module_name), args=[object.id])
        return "<a href='%s'>%s</a>" % (str(url), object.first_name + ' ' + object.last_name)

    project_owner.allow_tags = True

admin.site.register(Project, ProjectAdmin)

