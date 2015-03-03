from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete
from django.utils.translation import ugettext as _
from django.utils import translation
from django.template.loader import render_to_string

from bluebottle.utils.model_dispatcher import get_taskmember_model
from bluebottle.clients.context import ClientContext
from bluebottle.clients.utils import tenant_url

from bluebottle.clients.mail import EmailMultiAlternatives

TASK_MEMBER_MODEL = get_taskmember_model()


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

    def send(self):
        translation.activate(self.receiver.primary_language)
        translation.deactivate()
        text_content = render_to_string('{0}.txt'.format(self.template_mail), context_instance=self.ctx)
        html_content = render_to_string('{0}.html'.format(self.template_mail), context_instance=self.ctx)
        msg = EmailMultiAlternatives(subject=self.subject, body=text_content, to=[self.receiver.email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()


class TaskMemberAppliedMail(TaskMemberMailSender):

    def __init__(self, instance, *args, **kwargs):
        TaskMemberMailSender.__init__(self, instance, *args, **kwargs)

        self.template_mail = 'task_member_applied.mail'
        self.receiver = self.task.author
        self.subject = _('{0} applied for your task'.format(self.task_member.member.get_short_name()))
        self.ctx = ClientContext({'task': self.task, 'receiver': self.receiver, 'sender': self.task_member.member, 'link': self.task_link,
                            'site': self.site, 'motivation': self.task_member.motivation})


class TaskMemberRejectMail(TaskMemberMailSender):

    def __init__(self, instance, *args, **kwargs):
        TaskMemberMailSender.__init__(self, instance, *args, **kwargs)

        self.template_mail = 'task_member_rejected.mail'
        self.receiver = self.task_member.member
        self.subject = _('{0} didn\'t select you for a task'.format(self.task.author.get_short_name()))
        self.ctx = ClientContext({'task': self.task, 'receiver': self.receiver, 'sender': self.task.author, 'link': self.task_link,
                            'site': self.site, 'task_list': self.task_list})


class TaskMemberAcceptedMail(TaskMemberMailSender):

    def __init__(self, instance, *args, **kwargs):
        TaskMemberMailSender.__init__(self, instance, *args, **kwargs)

        self.template_mail = 'task_member_accepted.mail'
        self.receiver = self.task_member.member
        self.subject = _('{0} assigned you to a task'.format(self.task.author.get_short_name()))
        self.ctx = ClientContext({'task': self.task, 'receiver': self.receiver, 'sender': self.task.author, 'link': self.task_link,
                            'site': self.site})


class TaskMemberRealizedMail(TaskMemberMailSender):

    def __init__(self, instance, *args, **kwargs):
        TaskMemberMailSender.__init__(self, instance, *args, **kwargs)

        self.template_mail = 'task_member_realized.mail'
        self.receiver = self.task_member.member
        self.subject = _('You realised a task!'.format(self.task.project.title))
        self.ctx = ClientContext({'task': self.task, 'receiver': self.receiver, 'sender': self.task.author, 'link': self.task_link,
                            'site': self.site, 'task_list': self.task_list,
                            'project_link': self.project_link})


class TaskMemberWithdrawMail(TaskMemberMailSender):

    def __init__(self, instance, *args, **kwargs):
        TaskMemberMailSender.__init__(self, instance, *args, **kwargs)

        self.template_mail = 'task_member_withdrew.mail'
        self.receiver = self.task.author
        self.subject = _('{0} withdrew from a task').format(self.task_member.member.get_short_name())
        self.ctx = ClientContext({'task': self.task, 'receiver': self.receiver, 'sender': self.task_member.member,
                            'link': self.task_link, 'site': self.site, 'task_list': self.task_list, 'project_link': self.project_link})


class TaskMemberMailAdapter:
    """
    This class retrieve the correct TaskMemberMailSender instance based on the status and
    allows to send task emails.
    """

    TASK_MEMBER_MAIL = {
        TASK_MEMBER_MODEL.TaskMemberStatuses.applied: TaskMemberAppliedMail,
        TASK_MEMBER_MODEL.TaskMemberStatuses.rejected: TaskMemberRejectMail,
        TASK_MEMBER_MODEL.TaskMemberStatuses.accepted: TaskMemberAcceptedMail,
        TASK_MEMBER_MODEL.TaskMemberStatuses.realized: TaskMemberRealizedMail,
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


@receiver(post_save, weak=False, sender=TASK_MEMBER_MODEL)
def new_reaction_notification(sender, instance, created, **kwargs):

    mailer = TaskMemberMailAdapter(instance)
    mailer.send_mail()


@receiver(pre_delete, weak=False, sender=TASK_MEMBER_MODEL)
def task_member_withdraw(sender, instance, **kwargs):

    mailer = TaskMemberMailAdapter(instance, 'withdraw')
    mailer.send_mail()
