from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from parler.admin import TranslatableAdmin

from bluebottle.tasks.models import Skill


class SkillAdmin(TranslatableAdmin):
    list_display = ('name', 'task_link', 'member_link')
    readonly_fields = ('task_link', 'member_link')
    fields = readonly_fields + ('name', 'disabled', 'description', 'expertise')
    ordering = ('translations__name',)

    def get_actions(self, request):
        actions = super(SkillAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        if obj and obj.assignment_set.count() == 0:
            return True
        return False

    def task_link(self, obj):
        url = "{}?expertise_filter={}".format(reverse('admin:assignments_assignment_changelist'), obj.id)
        return format_html(
            "<a href='{}'>{} {}</a>",
            url, obj.assignment_set.count(), _('tasks')
        )
    task_link.short_description = _('Tasks with this skill')

    def member_link(self, obj):
        url = "{}?skills__id__exact={}".format(reverse('admin:members_member_changelist'), obj.id)
        return format_html(
            "<a href='{}'>{} {}</a>",
            url, obj.member_set.count(), _('users')
        )
    member_link.short_description = _('Users with this skill')


admin.site.register(Skill, SkillAdmin)
