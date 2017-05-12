from celery import shared_task

from django.dispatch import receiver
from django.db import connection
from django.db.models.signals import post_save, pre_delete
from django.utils import translation
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe

from tenant_extras.utils import TenantLanguage

from bluebottle.clients.utils import tenant_url, LocalTenant
from bluebottle.tasks.models import TaskMember
from bluebottle.surveys.models import Survey
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

        survey_url = Survey.url(self.task)

        self.ctx = {'task': self.task, 'receiver': self.receiver,
                    'sender': self.task.author,
                    'link': self.task_link,
                    'survey_link': mark_safe(survey_url) if survey_url else None,
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
        TaskMember.TaskMemberStatuses.withdrew: TaskMemberWithdrawMail,
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


@shared_task
def send_task_realized_mail(task, template, subject, tenant):
    """ Send an email to the task owner with the request to confirm
    the task participants.
    """
    connection.set_tenant(tenant)

    with LocalTenant(tenant, clear_tenant=True):
        if len(task.members.filter(status=TaskMember.TaskMemberStatuses.realized)):
            # There is already a confirmed task member: Do not bother the owner
            return

        send_mail(
            template_name='tasks/mails/{}.mail'.format(template),
            subject=subject,
            title=task.title,
            to=task.author,
            site=tenant_url(),
            link='/go/tasks/{0}'.format(task.id)
        )


@shared_task
def send_deadline_to_apply_passed_mail(task, subject, tenant):
    connection.set_tenant(tenant)

    with LocalTenant(tenant, clear_tenant=True):
        if not task.members_applied:
            template = 'deadline_to_apply_closed'
        else:
            if task.people_applied + task.externals_applied < task.people_needed:
                status = 'partial'
            elif task.people_accepted < task.people_needed:
                status = 'accept'
            else:
                status = 'target_reached'

            template = 'deadline_to_apply_{type}_{status}'.format(
                type=task.type, status=status
            )

        send_mail(
            template_name='tasks/mails/{}.mail'.format(template),
            subject=subject,
            task=task,
            to=task.author,
            site=tenant_url(),
            edit_link='/tasks/{0}/edit'.format(task.id),
            link='/tasks/{0}'.format(task.id),

        )


@receiver(post_save, weak=False, sender=TaskMember)
def new_reaction_notification(sender, instance, created, **kwargs):
    if instance.status != instance._original_status or created:
        mailer = TaskMemberMailAdapter(instance)
        mailer.send_mail()


@receiver(pre_delete, weak=False, sender=TaskMember)
def task_member_withdraw(sender, instance, **kwargs):
    mailer = TaskMemberMailAdapter(instance, 'withdraw')
    mailer.send_mail()
