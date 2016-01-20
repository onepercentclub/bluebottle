from django.utils.translation import ugettext as _
from django.utils.timezone import now

from bluebottle.bb_tasks.models import BaseTask, BaseTaskMember, BaseTaskFile, \
    BaseSkill
from bluebottle.clients.utils import tenant_url
from bluebottle.utils.email_backend import send_mail
from bluebottle.clients import properties
from bluebottle.bb_metrics.utils import bb_track

from tenant_extras.utils import TenantLanguage

GROUP_PERMS = {
    'Staff': {
        'perms': (
            'add_task', 'change_task', 'delete_task',
            'add_taskmember', 'change_taskmember', 'delete_taskmember',
        )
    }
}

class Task(BaseTask):
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
    pass


class TaskFile(BaseTaskFile):
    pass
