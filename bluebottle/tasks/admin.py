from datetime import timedelta

from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from daterange_filter.filter import DateRangeFilter

from bluebottle.tasks.models import TaskMember, TaskFile, Task, Skill
from bluebottle.utils.admin import export_as_csv_action


# Bulk actions for Task
def mark_as_open(modeladmin, request, queryset):
    queryset.update(status='open')


mark_as_open.short_description = _("Mark selected Tasks as Open")


def mark_as_in_progress(modeladmin, request, queryset):
    queryset.update(status='in progress')


mark_as_in_progress.short_description = _("Mark selected Tasks as Running")


def mark_as_closed(modeladmin, request, queryset):
    queryset.update(status='closed')


mark_as_closed.short_description = _("Mark selected Tasks as Done")


def mark_as_realized(modeladmin, request, queryset):
    queryset.update(status='realized')


mark_as_realized.short_description = _("Mark selected Tasks as Realised")


# Bulk actions for Task Member
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


mark_as_stopped.short_description = _("Mark selected Task Members as Withdrew")


def mark_as_tm_realized(modeladmin, request, queryset):
    queryset.update(status='realized')


mark_as_tm_realized.short_description = _("Mark selected Task Members as Realised")


def resume_link(obj):
    if obj.resume:
        url = reverse(
            'task-member-resume',
            args=[obj.id]
        )
        return format_html(
            u"<a href='{}'>{}</a>",
            str(url), _('Resume')
        )


class TaskMemberAdminInline(admin.StackedInline):
    model = TaskMember
    extra = 0
    raw_id_fields = ('member',)
    readonly_fields = ('created',)
    fields = readonly_fields + ('member', 'status', 'motivation',
                                'time_spent', 'externals', 'resume')

    def resume_link(self, obj):
        return resume_link(obj)


class TaskFileAdminInline(admin.StackedInline):
    model = TaskFile

    raw_id_fields = ('author',)
    readonly_fields = ('created',)
    fields = readonly_fields + ('author', 'file')
    extra = 0


class DeadlineToAppliedFilter(admin.SimpleListFilter):
    title = _('Deadline to apply')
    parameter_name = 'deadline_to_apply'

    def lookups(self, request, model_admin):
        return (
            ('7', 'Next 7 days'),
            ('30', 'Next 30 days'),
            ('0', 'Deadline passed')
        )

    def queryset(self, request, queryset):
        if self.value() is not None:
            days = int(self.value())
            if days > 0:
                return queryset.filter(
                    deadline_to_apply__gt=now(),
                    deadline_to_apply__lt=now() + timedelta(days=days)
                )
            else:
                return queryset.filter(
                    deadline_to_apply__lt=now()
                )
        else:
            return queryset


class OnlineOnLocationFilter(admin.SimpleListFilter):
    title = _('Online or on location')
    parameter_name = 'online'

    def lookups(self, request, model_admin):
        return (
            ('online', 'Online'),
            ('on_location', 'On location'),
        )

    def queryset(self, request, queryset):
        value = self.value()

        if value == 'online':
            queryset = queryset.filter(location__isnull=True)

        if value == 'on_location':
            queryset = queryset.filter(location__isnull=False)

        return queryset


class TaskAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'

    inlines = (TaskMemberAdminInline, TaskFileAdminInline,)

    raw_id_fields = ('author', 'project')
    list_filter = ('status', 'type', 'skill__expertise',
                   OnlineOnLocationFilter,
                   ('skill', admin.RelatedOnlyFieldListFilter),
                   'deadline', ('deadline', DateRangeFilter),
                   DeadlineToAppliedFilter, ('deadline_to_apply', DateRangeFilter),
                   'accepting'
                   )
    list_display = ('title', 'project', 'status', 'created', 'deadline', 'expertise_based')

    readonly_fields = ('date_status_change',)

    search_fields = (
        'title', 'description',
        'author__first_name', 'author__last_name'
    )

    export_fields = (
        ('title', 'title'),
        ('project', 'project'),
        ('type', 'type'),
        ('status', 'status'),
        ('deadline', 'deadline'),
        ('deadline_to_apply', 'deadline to apply'),
        ('accepting', 'accepting'),
        ('needs_motivation', 'needs_motivation'),
        ('date_realized', 'date realized'),
        ('skill', 'skill'),
        ('people_needed', 'people needed'),
        ('time_needed', 'time needed'),
        ('author', 'author'),
        ('author__remote_id', 'remote id')
    )

    actions = [mark_as_open, mark_as_in_progress, mark_as_closed,
               mark_as_realized, export_as_csv_action(fields=export_fields)]

    fields = ('title', 'description', 'skill', 'time_needed', 'status',
              'accepting', 'needs_motivation', 'location',
              'date_status_change', 'people_needed',
              'project', 'author', 'type', 'deadline', 'deadline_to_apply')


admin.site.register(Task, TaskAdmin)


class TaskAdminInline(admin.TabularInline):
    model = Task
    extra = 0
    fields = ('title', 'project', 'status', 'deadline', 'deadline_to_apply',
              'time_needed', 'task_admin_link')
    readonly_fields = ('task_admin_link',)

    def task_admin_link(self, obj):
        object = obj
        url = reverse('admin:{0}_{1}_change'.format(
            object._meta.app_label, object._meta.model_name),
            args=[object.id])
        return format_html(
            u"<a href='{}'>{}</a>",
            str(url), obj.title.encode("utf8")
        )


class TaskMemberAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'

    raw_id_fields = ('member', 'task')
    list_filter = ('status',)
    list_display = ('member_email', 'task', 'status', 'updated')

    readonly_fields = ('updated', 'resume_link')

    search_fields = (
        'member__email',
    )

    fields = (
        'member', 'motivation',
        'status', 'updated',
        'time_spent', 'externals',
        'task', 'resume_link'
    )
    export_fields = (
        ('member__email', 'member_email'),
        ('member__remote_id', 'remote id'),
        ('task', 'task'),
        ('task__project', 'project'),
        ('task__project__location__name', 'location'),
        ('status', 'status'),
        ('updated', 'updated'),
        ('time_spent', 'time spent'),
        ('task__time_needed', 'time applied for')
    )

    actions = [mark_as_applied, mark_as_accepted, mark_as_rejected,
               mark_as_stopped, mark_as_tm_realized, export_as_csv_action(fields=export_fields)]

    def member_email(self, obj):
        return obj.member.email

    member_email.admin_order_field = 'member__email'
    member_email.short_description = "Member Email"

    def resume_link(self, obj):
        resume_link(obj)

    def lookup_allowed(self, key, value):
        if key in ('task__deadline__year',):
            return True

        return super(TaskMemberAdmin, self).lookup_allowed(key, value)


admin.site.register(TaskMember, TaskMemberAdmin)


class SkillAdmin(admin.ModelAdmin):
    list_display = ('translated_name', 'disabled', 'expertise')
    readonly_fields = ('translated_name',)
    fields = readonly_fields + ('disabled', 'description', 'expertise')

    def translated_name(self, obj):
        return _(obj.name)

    translated_name.short_description = _('Name')

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


admin.site.register(Skill, SkillAdmin)
