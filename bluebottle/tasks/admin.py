from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.forms import ModelForm
from django.forms.models import ModelChoiceField

from bluebottle.utils.model_dispatcher import (
    get_user_model, get_task_model, get_taskmember_model, get_taskfile_model,
    get_task_skill_model)

BB_USER_MODEL = get_user_model()
BB_TASK_MODEL = get_task_model()
BB_TASKMEMBER_MODEL = get_taskmember_model()
BB_TASKFILE_MODEL = get_taskfile_model()
BB_SKILL_MODEL = get_task_skill_model()

# Bulk actions for Task
def mark_as_open(modeladmin, request, queryset):
    queryset.update(status='open')
mark_as_open.short_description = _("Mark selected Tasks as Open")

def mark_as_in_progress(modeladmin, request, queryset):
    queryset.update(status='in progress')
mark_as_in_progress.short_description = _("Mark selected Tasks as In Progress")

def mark_as_closed(modeladmin, request, queryset):
    queryset.update(status='closed')
mark_as_closed.short_description = _("Mark selected Tasks as Closed")

def mark_as_realized(modeladmin, request, queryset):
    queryset.update(status='realized')
mark_as_realized.short_description = _("Mark selected Tasks as Realized")

#Bulk actions for Task Member

def mark_as_applied(modeladmin, request, queryset):
    queryset.update(status='applied')
mark_as_applied.short_description = _("Mark selected Task Members as Applied")

def mark_as_accepted(modeladmin, request, queryset):
    queryset.update(status='accepted')
mark_as_accepted.short_description = _("Mark selected Task Members as Accepted")

def mark_as_rejected(modeladmin, request, queryset):
    queryset.update(status='rejected')
mark_as_rejected.short_description = _("Mark selected Task Members as Rejected")

def mark_as_stopped(modeladmin, request, queryset):
    queryset.update(status='stopped')
mark_as_stopped.short_description = _("Mark selected Task Members as Stopped")

def mark_as_tm_realized(modeladmin, request, queryset):
    queryset.update(status='realized')
mark_as_tm_realized.short_description = _("Mark selected Task Members as Realized")


class TaskMemberAdminInline(admin.StackedInline):
    model = BB_TASKMEMBER_MODEL
    extra = 0
    raw_id_fields = ('member',)
    readonly_fields = ('created',)
    fields = readonly_fields + ('member', 'status', 'motivation',
                                'time_spent', 'externals')


class TaskFileAdminInline(admin.StackedInline):
    model = BB_TASKFILE_MODEL

    raw_id_fields = ('author',)
    readonly_fields = ('created',)
    fields = readonly_fields + ('author', 'file')
    extra = 0


class TaskForm(ModelForm):
    owner = ModelChoiceField(queryset=BB_USER_MODEL.objects.order_by('email'))

    class Meta:
        model = BB_TASK_MODEL


class TaskAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'

    inlines = (TaskMemberAdminInline, TaskFileAdminInline,)

    raw_id_fields = ('author', 'project')
    list_filter = ('status',)
    list_display = ('title', 'project', 'status', 'deadline')

    readonly_fields = ('date_status_change',)

    search_fields = (
        'title', 'description',
        'author__first_name', 'author__last_name'
    )
    actions = [mark_as_open, mark_as_in_progress, mark_as_closed,
               mark_as_realized]
    fields = ('title', 'description', 'skill', 'time_needed', 'status',
              'date_status_change', 'people_needed', 'project', 'author',
              'tags', 'deadline')


admin.site.register(BB_TASK_MODEL, TaskAdmin)


class TaskAdminInline(admin.TabularInline):
    model = BB_TASK_MODEL
    extra = 0
    fields = ('title', 'project', 'status', 'deadline', 'time_needed', 'task_admin_link')
    readonly_fields = ('task_admin_link', )

    def task_admin_link(self, obj):   
        object = obj
        url = reverse('admin:{0}_{1}_change'.format(
            object._meta.app_label, object._meta.module_name),
            args=[object.id])
        return "<a href='{0}'>{1}</a>".format(str(url), obj.title)

    task_admin_link.allow_tags = True


class TaskMemberAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'

    raw_id_fields = ('member', 'task')
    list_filter = ('status',)
    list_display = ('get_member_email', 'task', 'status', 'updated')

    readonly_fields = ('updated',)

    search_fields = (
        'member__email',
    )

    fields = (
        'member', 'motivation',
        'status', 'updated',
        'time_spent', 'externals',
        'task',
    )

    actions = [mark_as_applied, mark_as_accepted, mark_as_rejected,
               mark_as_stopped, mark_as_tm_realized]


admin.site.register(BB_TASKMEMBER_MODEL, TaskMemberAdmin)
