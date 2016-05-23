from django.contrib import admin
from django.core.urlresolvers import reverse
from django.forms import ModelForm
from django.forms.models import ModelChoiceField

from bluebottle.members.models import Member
from bluebottle.tasks.models import TaskMember, TaskFile, Task


class TaskMemberAdminInline(admin.StackedInline):
    model = TaskMember
    extra = 0
    raw_id_fields = ('member',)
    readonly_fields = ('created',)
    fields = readonly_fields + ('member', 'status', 'motivation',
                                'time_spent', 'externals')


class TaskFileAdminInline(admin.StackedInline):
    model = TaskFile

    raw_id_fields = ('author',)
    readonly_fields = ('created',)
    fields = readonly_fields + ('author', 'file')
    extra = 0


class TaskForm(ModelForm):
    owner = ModelChoiceField(queryset=Member.objects.order_by('email'))

    class Meta:
        model = Task
        exclude = ()


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

    fields = ('title', 'description', 'skill', 'time_needed', 'status',
              'date_status_change', 'people_needed', 'project', 'author',
              'tags', 'deadline')


admin.site.register(Task, TaskAdmin)


class TaskAdminInline(admin.TabularInline):
    model = Task
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


admin.site.register(TaskMember, TaskMemberAdmin)
