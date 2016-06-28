from django.utils.translation import ugettext as _
from django.utils.timezone import now
from django.db.models.signals import pre_save

from bluebottle.bb_tasks.models import BaseTask, BaseTaskMember, BaseTaskFile, \
    BaseSkill
from bluebottle.bb_metrics.utils import bb_track
from bluebottle.clients import properties


GROUP_PERMS = {
    'Staff': {
        'perms': (
            'add_task', 'change_task', 'delete_task',
            'add_taskmember', 'change_taskmember', 'delete_taskmember',
        )
    }
}

class Task(BaseTask):
    def get_absolute_url(self):
        """ Get the URL for the current task. """
        return 'https://{}/tasks/{}'.format(properties.tenant.domain_url, self.id)

    # This could also belong to bb_tasks.models but we need the actual, non-abstract
    # model for the signal handling anyway. Eventually, tasks/bb_tasks will have to be
    # merged.
    def deadline_reached(self):
        """ The task deadline has been reached. Set it to realised and notify the
            owner """
        # send "The deadline of your task" - mail

        self.status = 'realized'
        self.save()

        data = {
            "Task": self.title,
            "Author": self.author.username
        }
        bb_track("Task Deadline Reached", data)

    def status_changed(self, oldstate, newstate):
        """ called by post_save signal handler, if status changed """
        # confirm everything with task owner

        if oldstate in ("in progress", "open") and newstate == "realized":

            if self.deadline < now():
                with TenantLanguage(self.author.primary_language):
                    subject = _("The deadline for task '{0}' has been reached").format(self.title)

                send_mail(
                    template_name="tasks/mails/task_deadline_reached.mail",
                    subject=subject,
                    title=self.title,
                    to=self.author,
                    site=tenant_url(),
                    link='/go/tasks/{0}'.format(self.id)
                )

            with TenantLanguage(self.author.primary_language):
                subject = _("You've set '{0}' to realized").format(self.title)

            send_mail(
                template_name="tasks/mails/task_status_realized.mail",
                subject=subject,
                title=self.title,
                to=self.author,
                site=tenant_url(),
                link='/go/tasks/{0}'.format(self.id)
            )

        if oldstate in ("in progress", "open") and newstate in ("realized", "closed"):
            data = {
                "Task": self.title,
                "Author": self.author.username,
                "Old status": oldstate,
                "New status": newstate
            }

            bb_track("Task Completed", data)

    def save(self, *args, **kwargs):
        if not self.author_id:
            self.author = self.project.owner
        super(Task, self).save(*args, **kwargs)

from django.db.models.signals import post_init, post_save
from django.dispatch import receiver


# post_init to store state on model
@receiver(post_init, sender=Task,
          dispatch_uid="bluebottle.tasks.Task.post_init")
def task_post_init(sender, instance, **kwargs):
    instance._init_status = instance.status


# post save to check if changed?
@receiver(post_save, sender=Task,
          dispatch_uid="bluebottle.tasks.Task.post_save")
def task_post_save(sender, instance, **kwargs):
    try:
        if instance._init_status != instance.status:
            instance.status_changed(instance._init_status, instance.status)
    except AttributeError:
        pass


class Skill(BaseSkill):
    pass


class TaskMember(BaseTaskMember):
    def save(self, *args, **kwargs):
        super(TaskMember, self).save(*args, **kwargs)
        self.check_number_of_members_needed(self.task)

    # TODO: refactor this to use a signal and move code to task model
    def check_number_of_members_needed(self, task):
        members = TaskMember.objects.filter(task=task,
                                                        status='accepted')
        total_externals = 0
        for member in members:
            total_externals += member.externals

        members_accepted = members.count() + total_externals

        if task.status == 'open' and task.people_needed <= members_accepted:
            task.set_in_progress()
        return members_accepted

    @property
    def member_email(self):
        if self.member.email:
            return self.member.email
        return _("No email address for this user")

    @property
    def time_applied_for(self):
        return self.task.time_needed

    @property
    def project(self):
        return self.task.project


class TaskFile(BaseTaskFile):
    pass

@receiver(pre_save, weak=False, sender=TaskMember, dispatch_uid='set-hours-spent-taskmember')
def set_hours_spent_taskmember(sender, instance, **kwargs):
    if instance.status != instance._initial_status and instance.status == TaskMember.TaskMemberStatuses.realized:
        instance.time_spent = instance.task.time_needed

from bluebottle.bb_tasks.taskwallmails import *
from bluebottle.bb_tasks.taskmail import *
