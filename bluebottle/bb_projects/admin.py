from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from parler.admin import TranslatableAdmin

from bluebottle.bb_projects.models import ProjectTheme


@admin.register(ProjectTheme)
class ProjectThemeAdmin(TranslatableAdmin):
    list_display = admin.ModelAdmin.list_display + ('slug', 'disabled', 'initiative_link')
    readonly_fields = ('initiative_link',)
    fields = ('name', 'slug', 'description', 'disabled') + readonly_fields
    ordering = ('translations__name',)

    def initiative_link(self, obj):
        url = "{}?theme__id__exact={}".format(reverse('admin:initiatives_initiative_changelist'), obj.id)
        return format_html("<a href='{}'>{} initiatives</a>".format(url, obj.initiative_set.count()))

    initiative_link.short_description = _('Initiatives')
