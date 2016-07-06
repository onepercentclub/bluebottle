from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete
from django.utils.translation import ugettext as _
from django.utils import translation

from tenant_extras.utils import TenantLanguage

from bluebottle.clients.utils import tenant_url
from bluebottle.tasks.models import TaskMember
from bluebottle.utils.email_backend import send_mail


class TaskMemberMailSender:
    """
    The base class for Task Mail senders
    """

    def __init__(self, instance, *args, **kwargs):
        self.task_member = instance
        self.task = instance.task
        self.task_link = '/go/tasks/{0}'.format(self.task.id)
        self.site = tenant_url()
        self.task_list = '/go/tasks'
        self.project_link = '/go/projects/{0}'.format(self.task.project.slug)
        self.cur_language = translation.get_language()

    def send(self):
        send_mail(template_name=self.template_mail, subject=self.subject,
                  to=self.receiver, **self.ctx)


class TaskMemberAppliedMail(TaskMemberMailSender):
    def __init__(self, instance, *args, **kwargs):
        TaskMemberMailSender.__init__(self, instance, *args, **kwargs)
        self.template_mail = 'task_member_applied.mail'
        self.receiver = self.task.author

        with TenantLanguage(self.task_member.member.primary_language):
            self.subject = _('%(member)s applied for your task') % {
                'member': self.task_member.member.get_short_name()}

        self.ctx = {'task': self.task, 'receiver': self.receiver,
                    'sender': self.task_member.member,
                    'link': self.task_link,
                    'site': self.site,
                    'motivation': self.task_member.motivation}


class TaskMemberRejectMail(TaskMemberMailSender):
    def __init__(self, instance, *args, **kwargs):
        TaskMemberMailSender.__init__(self, instance, *args, **kwargs)

        self.template_mail = 'task_member_rejected.mail'
        self.receiver = self.task_member.member

        with TenantLanguage(self.receiver.primary_language):
            self.subject = _('%(author)s didn\'t select you for a task') % {
                'author': self.task.author.get_short_name()}

        self.ctx = {'task': self.task, 'receiver': self.receiver,
                    'sender': self.task.author,
                    'link': self.task_link,
                    'site': self.site,
                    'task_list': self.task_list}


class TaskMemberAcceptedMail(TaskMemberMailSender):
    def __init__(self, instance, *args, **kwargs):
        TaskMemberMailSender.__init__(self, instance, *args, **kwargs)

        self.template_mail = 'task_member_accepted.mail'
        self.receiver = self.task_member.member

        with TenantLanguage(self.receiver.primary_language):
            self.subject = _('%(author)s assigned you to a task') % {
                'author': self.task.author.get_short_name()}

        self.ctx = {'task': self.task, 'receiver': self.receiver,
                    'sender': self.task.author,
                    'link': self.task_link,
                    'site': self.site}


class TaskMemberRealizedMail(TaskMemberMailSender):
    def __init__(self, instance, *args, **kwargs):
        TaskMemberMailSender.__init__(self, instance, *args, **kwargs)

        self.template_mail = 'task_member_realized.mail'
        self.receiver = self.task_member.member

        with TenantLanguage(self.receiver.primary_language):
            self.subject = _('You realised a task!')

        self.ctx = {'task': self.task, 'receiver': self.receiver,
                    'sender': self.task.author,
                    'link': self.task_link,
                    'site': self.site,
                    'task_list': self.task_list,
                    'project_link': self.project_link}


class TaskMemberWithdrawMail(TaskMemberMailSender):
    def __init__(self, instance, *args, **kwargs):
        TaskMemberMailSender.__init__(self, instance, *args, **kwargs)

        self.template_mail = 'task_member_withdrew.mail'
        self.receiver = self.task.author

        with TenantLanguage(self.receiver.primary_language):
            self.subject = _('%(member)s withdrew from a task') % {
                'member': self.task_member.member.get_short_name()}

        self.ctx = {'task': self.task, 'receiver': self.receiver,
                    'sender': self.task_member.member,
                    'link': self.task_link, 'site': self.site,
                    'task_list': self.task_list,
                    'project_link': self.project_link}


class TaskMemberMailAdapter:
    """
    This class retrieve the correct TaskMemberMailSender instance based on
    the status and allows to send task emails.
    """

    TASK_MEMBER_MAIL = {
        TaskMember.TaskMemberStatuses.applied: TaskMemberAppliedMail,
        TaskMember.TaskMemberStatuses.rejected: TaskMemberRejectMail,
        TaskMember.TaskMemberStatuses.accepted: TaskMemberAcceptedMail,
        TaskMember.TaskMemberStatuses.realized: TaskMemberRealizedMail,
        'withdraw': TaskMemberWithdrawMail,
    }

    mail_sender = None

    def __init__(self, instance, status=None):

        if not status:
            status = instance.status
        # If a mailer is provided for the task status, set the mail_sender
        if self.TASK_MEMBER_MAIL.get(status):
            self.mail_sender = self.TASK_MEMBER_MAIL.get(status)(instance)

    def send_mail(self):
        if self.mail_sender:
            self.mail_sender.send()


@receiver(post_save, weak=False, sender=TaskMember)
def new_reaction_notification(sender, instance, created, **kwargs):
    mailer = TaskMemberMailAdapter(instance)
    mailer.send_mail()


@receiver(pre_delete, weak=False, sender=TaskMember)
def task_member_withdraw(sender, instance, **kwargs):
    mailer = TaskMemberMailAdapter(instance, 'withdraw')
    mailer.send_mail()
