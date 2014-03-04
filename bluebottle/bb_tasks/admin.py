from django.contrib.auth import get_user_model
from django.contrib import admin
from django.forms import ModelForm
from django.forms.models import ModelChoiceField

from bluebottle.utils.utils import get_task_model, get_taskmember_model, get_taskfile_model, get_skill_model

BB_USER_MODEL = get_user_model()
BB_TASK_MODEL = get_task_model()
BB_TASKMEMBER_MODEL = get_taskmember_model()
BB_TASKFILE_MODEL = get_taskfile_model()
BB_SKILL_MODEL = get_skill_model

class TaskMemberAdminInline(admin.StackedInline):
    model = BB_TASKMEMBER_MODEL

    raw_id_fields = ('member', )
    readonly_fields = ('created', )
    fields =  readonly_fields + ('member', 'status', 'motivation', 'time_spent')
    extra = 0


class TaskFileAdminInline(admin.StackedInline):
    model = BB_TASKFILE_MODEL

    raw_id_fields = ('author', )
    readonly_fields = ('created', )
    fields =  readonly_fields + ('author', 'file')
    extra = 0


class TaskForm(ModelForm):
    owner = ModelChoiceField(queryset=BB_USER_MODEL.objects.order_by('email'))

    class Meta:
        model = BB_TASK_MODEL


class TaskAdmin(admin.ModelAdmin):

    date_hierarchy = 'created'

    inlines = (TaskMemberAdminInline, TaskFileAdminInline, )

    raw_id_fields = ('author', 'project')
    list_filter = ('status', )
    list_display = ('title', 'project', 'status', 'date_status_change')

    readonly_fields = ('date_status_change',)

    search_fields = (
        'title', 'description',
        'author__first_name', 'author__last_name'
    )
    # ordering
    fields = (
        'title', 'description',
        'skill', 'time_needed',
        'status', 'date_status_change',
        'people_needed',
        'project', 'author',
        'tags',
        'deadline',
    )

admin.site.register(BB_TASK_MODEL, TaskAdmin)
