from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from parler.admin import TranslatableAdmin

from bluebottle.tasks.models import Skill


class SkillAdmin(TranslatableAdmin):
    list_display = ('name', 'member_link')
    readonly_fields = ('member_link',)
    fields = readonly_fields + ('name', 'disabled', 'description', 'expertise')
    ordering = ('translations__name',)

    def get_actions(self, request):
        actions = super(SkillAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def member_link(self, obj):
        url = "{}?skills__id__exact={}".format(reverse('admin:members_member_changelist'), obj.id)
        return format_html(
            "<a href='{}'>{} {}</a>",
            url, obj.member_set.count(), _('users')
        )
    member_link.short_description = _('Users with this skill')


admin.site.register(Skill, SkillAdmin)
