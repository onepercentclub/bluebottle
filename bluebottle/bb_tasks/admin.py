from django.contrib.auth import get_user_model
from django.contrib import admin
from django.forms import ModelForm
from django.forms.models import ModelChoiceField

from . import get_task_model
from .models import TaskMember, TaskFile, Skill

BB_USER_MODEL = get_user_model()
BB_TASK_MODEL = get_task_model()


class TaskMemberInline(admin.StackedInline):
    model = BB_TASK_MODEL.members.through


class TaskFileInLine(admin.StackedInline):
    model = BB_TASK_MODEL.files.through


# class TaskMemberAdmin(admin.StackedInline):
#     raw_id_fields = ('member', )
#     readonly_fields = ('created', )
#     fields = readonly_fields + ('member', 'status', 'motivation')
#     extra = 0
#
#
# class TaskFileAdmin(admin.StackedInline):
#     raw_id_fields = ('author', )
#     readonly_fields = ('created', )
#     fields = readonly_fields + ('author', 'file')
#     extra = 0
#

class TaskForm(ModelForm):
    owner = ModelChoiceField(queryset=BB_USER_MODEL.objects.order_by('email'))

    class Meta:
        model = BB_TASK_MODEL


class TaskAdmin(admin.ModelAdmin):

    date_hierarchy = 'created'

    inlines = (TaskMemberInline, TaskFileInLine, )

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
        'project', 'author',
        'tags',
        'deadline',
    )

admin.site.register(BB_TASK_MODEL, TaskAdmin)


class SkillAdmin(admin.ModelAdmin):
    model = Skill

admin.site.register(Skill, SkillAdmin)
