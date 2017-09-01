from datetime import timedelta
from django.db.models.signals import post_init
from django.db.models import Sum

from exportdb.exporter import ExportModelResource

from bluebottle.projects.models import project_post_init, Project
from bluebottle.utils.signals import temp_disconnect_signal
from bluebottle.tasks.models import task_post_init, Task


class DateRangeResource(ExportModelResource):
    range_field = 'created'
    select_related = None

    def get_queryset(self):
        qs = super(DateRangeResource, self).get_queryset()
        if self.select_related:
            qs = qs.select_related(*self.select_related)
        frm, to = self.kwargs.get('from_date'), self.kwargs.get('to_date')
        to = to + timedelta(days=1)

        return qs.filter(**{'%s__range' % self.range_field: (frm, to)})


class UserResource(DateRangeResource):
    range_field = 'date_joined'
    select_related = ('location', 'location__group')


class ProjectResource(DateRangeResource):
    select_related = ('status', 'owner', 'location', 'location__group', 'theme')

    def get_queryset(self):
        return super(ProjectResource, self).get_queryset().annotate(
            time_spent=Sum('task__members__time_spent')
        )

    def export(self, **kwargs):
        with temp_disconnect_signal(
                signal=post_init,
                receiver=project_post_init,
                sender=Project,
                dispatch_uid='bluebottle.projects.Project.post_init'):
            data = super(ProjectResource, self).export(**kwargs)
        return data


class TaskResource(DateRangeResource):
    select_related = ('project', 'author')

    def export(self, **kwargs):
        task_signal = dict(
            signal=post_init,
            receiver=task_post_init,
            sender=Task,
            dispatch_uid='bluebottle.tasks.Task.post_init'
        )
        project_signal = dict(
            signal=post_init,
            receiver=project_post_init,
            sender=Project,
            dispatch_uid='bluebottle.projects.Project.post_init'
        )
        with temp_disconnect_signal(**task_signal), temp_disconnect_signal(
                **project_signal):
            data = super(TaskResource, self).export(**kwargs)
        return data


class TaskMemberResource(DateRangeResource):
    select_related = ('member', 'task', 'task__project', 'member__location',
                      'member__location__group', 'task__project__location',
                      'task__project__location__group')

    def export(self, **kwargs):
        task_signal = dict(
            signal=post_init,
            receiver=task_post_init,
            sender=Task,
            dispatch_uid='bluebottle.tasks.Task.post_init'
        )
        project_signal = dict(
            signal=post_init,
            receiver=project_post_init,
            sender=Project,
            dispatch_uid='bluebottle.projects.Project.post_init'
        )
        with temp_disconnect_signal(**task_signal), temp_disconnect_signal(
                **project_signal):
            data = super(TaskMemberResource, self).export(**kwargs)
        return data


class DonationResource(DateRangeResource):
    select_related = ('order', 'order__user', 'order__user__location', 'order__user__location__group',
                      'project', 'project', 'fundraiser')

    def export(self, **kwargs):
        with temp_disconnect_signal(
                signal=post_init,
                receiver=project_post_init,
                sender=Project,
                dispatch_uid='bluebottle.projects.Project.post_init'):
            data = super(DonationResource, self).export(**kwargs)
        return data
