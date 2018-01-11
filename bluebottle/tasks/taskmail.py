from celery import shared_task

from django.dispatch import receiver
from django.db import connection
from django.db.models.signals import pre_save, pre_delete, post_save
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe

from tenant_extras.utils import TenantLanguage

from bluebottle.clients.utils import tenant_url, LocalTenant
from bluebottle.tasks.models import TaskMember, Task
from bluebottle.surveys.models import Survey
from bluebottle.utils.email_backend import send_mail


TASK_REMINDER_INTERVAL = 5


class TaskMemberMailSender:
    """
    The base class for Task Mail senders
    """

    def __init__(self, instance, message=None, *args, **kwargs):
        self.task_member = instance
        self.task = instance.task

        self.ctx = {
            'task': self.task,
            'message': message,
            'receiver': self.receiver,
            'sender': self.sender,
            'link': '/go/tasks/{0}'.format(self.task.id),
            'site': tenant_url(),
            'project_list': '/projects',
            'project_link': '/projects/{0}'.format(self.task.project.slug),
        }

    @property
    def receiver(self):
        return self.task_member.member

    @property
    def sender(self):
        return self.task.author

    def send(self):
        send_mail(template_name=self.template_name, subject=self.subject,
                  to=self.receiver, **self.ctx)


class TaskMemberAppliedMail(TaskMemberMailSender):
    template_name = 'task_member_applied.mail'

    def __init__(self, *args, **kwargs):
        TaskMemberMailSender.__init__(self, *args, **kwargs)
        self.ctx['motivation'] = self.task_member.motivation

    @property
    def subject(self):
        with TenantLanguage(self.task_member.member.primary_language):
            return _('%(member)s applied for your task') % {
                'member': self.task_member.member.get_short_name()}

    @property
    def receiver(self):
        return self.task.author

    @property
    def sender(self):
        return self.task_member.member


class TaskMemberRejectMail(TaskMemberMailSender):
    template_name = 'task_member_rejected.mail'

    @property
    def subject(self):
        with TenantLanguage(self.receiver.primary_language):
            return _('%(author)s didn\'t select you for a task') % {
                'author': self.task.author.get_short_name()}


class TaskMemberAcceptedMail(TaskMemberMailSender):
    template_name = 'task_member_accepted.mail'

    @property
    def subject(self):
        with TenantLanguage(self.receiver.primary_language):
            return _('%(author)s assigned you to a task') % {
                'author': self.task.author.get_short_name()}


class TaskMemberJoinedMail(TaskMemberMailSender):
    template_name = 'task_member_joined.mail'

    def __init__(self, *args, **kwargs):
        TaskMemberMailSender.__init__(self, *args, **kwargs)
        self.ctx['motivation'] = self.task_member.motivation

    @property
    def subject(self):
        with TenantLanguage(self.task_member.member.primary_language):
            return _('%(member)s joined your task') % {
                'member': self.task_member.member.get_short_name()}

    @property
    def receiver(self):
        return self.task.author

    @property
    def sender(self):
        return self.task_member.member


class TaskMemberRealizedMail(TaskMemberMailSender):
    template_name = 'task_member_realized.mail'

    def __init__(self, *args, **kwargs):
        TaskMemberMailSender.__init__(self, *args, **kwargs)

        survey_url = Survey.url(self.task)
        self.ctx['survey_link'] = mark_safe(survey_url) if survey_url else None

    @property
    def subject(self):
        with TenantLanguage(self.receiver.primary_language):
            return _('You realised a task!')


class TaskMemberWithdrawMail(TaskMemberMailSender):
    template_name = 'task_member_withdrew.mail'

    @property
    def subject(self):
        with TenantLanguage(self.receiver.primary_language):
            return _('%(member)s withdrew from a task') % {
                'member': self.task_member.member.get_short_name()}

    @property
    def receiver(self):
        return self.task.author

    @property
    def sender(self):
        return self.task_member.member


class TaskMemberReminderMail(TaskMemberMailSender):

    def __init__(self, *args, **kwargs):
        TaskMemberMailSender.__init__(self, *args, **kwargs)
        self.ctx['task_reminder_interval'] = TASK_REMINDER_INTERVAL

    @property
    def template_name(self):
        if self.task.type == Task.TaskTypes.event:
            return 'task_member_reminder_event.mail'
        return 'task_member_reminder_ongoing.mail'

    @property
    def subject(self):
        with TenantLanguage(self.receiver.primary_language):
            return _('The task you subscribed to is due')


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

    def __init__(self, instance, status=None, message=None):
        if not status:
            status = instance.status
        # If a mailer is provided for the task status, set the mail_sender
        if self.TASK_MEMBER_MAIL.get(status):
            self.mail_sender = self.TASK_MEMBER_MAIL.get(status)(instance, message)

        # Set up some special mail rules for Tasks with auto accepting
        if instance.task.accepting == Task.TaskAcceptingChoices.automatic:
            if instance.status == TaskMember.TaskMemberStatuses.accepted:
                # Task member was auto-accepted
                self.mail_sender = TaskMemberJoinedMail(instance, message)

    def send_mail(self):
        if self.mail_sender:
            self.mail_sender.send()


@shared_task
def send_upcoming_task_reminder(task):
    # Acceptable statuses for task reminders
    statuses = [TaskMember.TaskMemberStatuses.accepted]

    # Send all applicable task members a mail if not send yet
    if not task.mail_logs.filter(type='upcoming_deadline').exists():
        for taskmember in task.members.filter(status__in=statuses).all():
            TaskMemberReminderMail(taskmember).send()
        task.mail_logs.create(type='upcoming_deadline')


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

        if not task.mail_logs.filter(type='deadline_to_apply_passed').exists():
            send_mail(
                template_name='tasks/mails/{}.mail'.format(template),
                subject=subject,
                task=task,
                to=task.author,
                site=tenant_url(),
                edit_link='/tasks/{0}/edit'.format(task.id),
                link='/tasks/{0}'.format(task.id),

            )
            task.mail_logs.create(type='deadline_to_apply_passed')


@receiver(post_save, weak=False, sender=TaskMember)
def new_reaction_notification(sender, instance, created, **kwargs):
    if (
        instance.status != instance._original_status and
        not getattr(instance, 'skip_mail', False) or
        created
    ):
        mailer = TaskMemberMailAdapter(instance)
        mailer.send_mail()


@receiver(pre_save, weak=False, sender=Task)
def email_deadline_update(sender, instance, **kwargs):
    if instance.pk:
        previous_instance = Task.objects.get(pk=instance.pk)
        if (previous_instance.deadline.date() != instance.deadline.date() and
                instance.status not in (Task.TaskStatuses.realized, Task.TaskStatuses.closed)):
            for task_member in instance.members_applied:

                with TenantLanguage(task_member.member.primary_language):
                    subject = _('The deadline of your task is changed')

                send_mail(
                    template_name='tasks/mails/deadline_changed.mail',
                    subject=subject,
                    title=instance.title,
                    original_date=previous_instance.deadline,
                    date=instance.deadline,
                    to=task_member.member,
                    site=tenant_url(),
                    link='/tasks/{0}'.format(instance.id)
                )


@receiver(pre_delete, weak=False, sender=TaskMember)
def task_member_withdraw(sender, instance, **kwargs):
    mailer = TaskMemberMailAdapter(instance, 'withdraw')
    mailer.send_mail()
