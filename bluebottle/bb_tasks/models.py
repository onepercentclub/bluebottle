from django.core.mail import EmailMultiAlternatives, get_connection
from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
import django.db.models.options as options
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.template.loader import get_template, render_to_string
from django.template import Context
from django.utils.translation import ugettext as _
from django.utils import translation

from django_extensions.db.fields import (
    ModificationDateTimeField, CreationDateTimeField)
from djchoices.choices import DjangoChoices, ChoiceItem
from taggit.managers import TaggableManager

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('default_serializer',)


class BaseSkill(models.Model):

    name = models.CharField(_('english name'), max_length=100, unique=True)
    name_nl = models.CharField(_('dutch name'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('id', )
        abstract = True

class BaseTaskMember(models.Model):
    class TaskMemberStatuses(DjangoChoices):
        applied = ChoiceItem('applied', label=_('Applied'))
        accepted = ChoiceItem('accepted', label=_('Accepted'))
        rejected = ChoiceItem('rejected', label=_('Rejected'))
        stopped = ChoiceItem('stopped', label=_('Stopped'))
        realized = ChoiceItem('realized', label=_('Realised'))

    member = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='%(app_label)s_%(class)s_related')
    task = models.ForeignKey(settings.TASKS_TASK_MODEL, related_name="members")
    status = models.CharField(
        _('status'), max_length=20, choices=TaskMemberStatuses.choices)

    motivation = models.TextField(
        _('Motivation'), help_text=_('Motivation by applicant.'), blank=True)
    comment = models.TextField(_('Comment'), help_text=_('Comment by task owner.'), blank=True)
    time_spent = models.PositiveSmallIntegerField(
        _('time spent'), default=0, help_text=_('Time spent executing this task.'))

    created = CreationDateTimeField(_('created'))
    updated = ModificationDateTimeField(_('updated'))

    _initial_status = None

    def __init__(self, *args, **kwargs):
        super(BaseTaskMember, self).__init__(*args, **kwargs)
        self._initial_status = self.status

    class Meta:
        abstract = True

class BaseTaskFile(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='%(app_label)s_%(class)s_related')
    title = models.CharField(max_length=255)
    file = models.FileField(_('file'), upload_to='task_files/')
    created = CreationDateTimeField(_('created'))
    updated = ModificationDateTimeField(_('Updated'))
    task = models.ForeignKey(settings.TASKS_TASK_MODEL, related_name="files")

    class Meta:
        abstract = True


class BaseTask(models.Model):
    """ The base Task model """

    class TaskStatuses(DjangoChoices):
        open = ChoiceItem('open', label=_('Open'))
        in_progress = ChoiceItem('in progress', label=_('In progress'))
        closed = ChoiceItem('closed', label=_('Closed'))
        realized = ChoiceItem('realized', label=_('Completed'))

    title = models.CharField(_('title'), max_length=100)
    description = models.TextField(_('description'))
    end_goal = models.TextField(_('end goal'))
    location = models.TextField(_('location'))

    project = models.ForeignKey(settings.PROJECTS_PROJECT_MODEL)
    # See Django docs on issues with related name and an (abstract) base class:
    # https://docs.djangoproject.com/en/dev/topics/db/models/#be-careful-with-related-name
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='%(app_label)s_%(class)s_related')
    status = models.CharField(
        _('status'), max_length=20, choices=TaskStatuses.choices,
        default=TaskStatuses.open)
    date_status_change = models.DateTimeField(_('date status change'), blank=True, null=True)

    deadline = models.DateTimeField()
    tags = TaggableManager(blank=True, verbose_name=_('tags'))

    # required resources
    time_needed = models.CharField(
        _('time_needed'), max_length=200,
        help_text=_('Estimated number of hours needed to perform this task.'))
    skill = models.ForeignKey(settings.TASKS_SKILL_MODEL, verbose_name=_('Skill needed'), null=True)

    # internal usage
    created = CreationDateTimeField(
        _('created'), help_text=_('When this task was created?'))
    updated = ModificationDateTimeField(_('updated'))

    objects = models.Manager()

    class Meta:
        default_serializer = 'bluebottle.bb_tasks.serializers.TaskSerializer'
        abstract = True
        ordering = ['-created']
        verbose_name = _(u'task')
        verbose_name_plural = _(u'tasks')

    def __init__(self, *args, **kwargs):
        super(BaseTask, self).__init__(*args, **kwargs)
        self._original_status = self.status

    def __unicode__(self):
        return self.title



from . import get_task_model, get_taskmember_model

TASK_MODEL = get_task_model()
TASK_MEMBER_MODEL = get_taskmember_model

class SupportedProjectsManager(models.Manager):
    """
    Manager to retrieve user statistics related to supported projects through
    tasks.
    """
    def by_user(self, user):
        """
        Fetches the projects supported by `user` by being a taskmember in the
        related tasks.

        Usage: Task.supported_projects.by_user(user) returns the projects
        queryset.
        """
        statuses = TASK_MEMBER_MODEL.TaskMemberStatuses

        valid_statuses = [
            statuses.applied, statuses.accepted, statuses.realized]
        projects = settings.PROJECTS_PROJECT_MODEL.objects.filter(
            task__taskmember__member=user,
            task__taskmember__status__in=valid_statuses).distinct()

        return projects


@receiver(post_save, weak=False, sender=TASK_MEMBER_MODEL)
def new_reaction_notification(sender, instance, created, **kwargs):
    task_member = instance
    task = instance.task

    site = 'https://' + Site.objects.get_current().domain

    # Project Wall Post
    if task_member.status == TASK_MEMBER_MODEL.TaskMemberStatuses.applied:
        receiver = task.author
        sender = task_member.member
        link = '/go/tasks/{0}'.format(task.id)

        # Compose the mail
        # Set the language for the receiver
        translation.activate(receiver.primary_language)
        subject = _('%(sender)s applied for your task.') % {'sender': sender.get_short_name()}
        ctx = Context({'task': task, 'receiver': receiver, 'sender': sender, 'link': link, 'site': site,
                       'motivation': task_member.motivation})
        text_content = render_to_string('task_member_applied.mail.txt', context_instance=ctx)
        html_content = render_to_string('task_member_applied.mail.html', context_instance=ctx)
        translation.deactivate()
        msg = EmailMultiAlternatives(subject=subject, body=text_content, to=[receiver.email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

    if task_member.status == TASK_MEMBER_MODEL.TaskMemberStatuses.rejected:
        sender = task.author
        receiver = task_member.member
        link = '/go/tasks/{0}'.format(task.id)

        # Compose the mail
        # Set the language for the receiver
        translation.activate(receiver.primary_language)
        subject = _('%(sender)s found someone else to do the task you applied for.') % {'sender': sender.get_short_name()}
        context = Context({'task': task, 'receiver': receiver, 'sender': sender, 'link': link, 'site': site})
        text_content = get_template('task_member_rejected.mail.txt').render(context)
        html_content = get_template('task_member_rejected.mail.html').render(context)
        translation.deactivate()
        msg = EmailMultiAlternatives(subject=subject, body=text_content, to=[receiver.email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

    if task_member.status == TASK_MEMBER_MODEL.TaskMemberStatuses.accepted:
        sender = task.author
        receiver = task_member.member
        link = '/go/tasks/{0}'.format(task.id)

        # Compose the mail
        # Set the language for the receiver
        translation.activate(receiver.primary_language)
        subject = _('%(sender)s accepted you to complete the tasks you applied for.') % {'sender': sender.get_short_name()}
        context = Context({'task': task, 'receiver': receiver, 'sender': sender, 'link': link, 'site': site})
        text_content = get_template('task_member_accepted.mail.txt').render(context)
        html_content = get_template('task_member_accepted.mail.html').render(context)
        translation.deactivate()
        msg = EmailMultiAlternatives(subject=subject, body=text_content, to=[receiver.email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()


def send_mail_task_realized(task):
    """
    Send (multiple) e-mails when a task is realized.
    The task members that weren't rejected are the receivers.
    """
    sender = task.author
    link = '/go/tasks/{0}'.format(task.id)
    site = 'https://' + Site.objects.get_current().domain

    qs = task.taskmember_set.exclude(status=TASK_MEMBER_MODEL.TaskMemberStatuses.rejected).select_related('member')
    receivers = [taskmember.member for taskmember in qs]

    emails = []

    for receiver in receivers:
        translation.activate(receiver.primary_language)
        subject = _('Good job! "%(task)s" is realized!.') % {'task': task.title}
        context = Context({'task': task, 'receiver': receiver, 'sender': sender, 'link': link, 'site': site})
        text_content = get_template('task_realized.mail.txt').render(context)
        html_content = get_template('task_realized.mail.html').render(context)
        translation.deactivate()
        msg = EmailMultiAlternatives(subject=subject, body=text_content, to=[receiver.email])
        msg.attach_alternative(html_content, "text/html")
        emails.append(msg)

    connection = get_connection()
    connection.send_messages(emails)
    connection.close()


#
#
# @receiver(m2m_changed, weak=False, sender=TASK_MODEL.members.through)
# def new_reaction_notification(sender, instance, **kwargs):
#     """
#     Signal receiver for new additions to the members of a task. It will set up
#     the ID of the related task in the ``TaskMember`` model and also send an
#     email to the task author to notify that a new member applied for the task.
#     """
#     if kwargs['action'] == 'post_add':
#         task_member_pk = kwargs['pk_set'].pop()
#         task_member = TASK_MEMBER_MODEL.objects.get(pk=task_member_pk)
#         task = instance
#
#         # Set up the ID of the related task here.
#         if not task_member.task_id:
#             task_member.task_id = task.pk
#             task_member.save()
#
#         site = 'https://' + Site.objects.get_current().domain
#
#         # Project Wall Post
#         if task_member.status == TASK_MEMBER_MODEL.TaskMemberStatuses.applied:
#             receiver = task.author
#             sender = task_member.member
#             link = '/go/tasks/{0}'.format(task.id)
#
#             # Compose the mail
#             # Set the language for the receiver
#             translation.activate(receiver.primary_language)
#             subject = _('{sender} applied for your task.'.format(sender=sender.get_short_name()))
#             ctx = Context({'task': task, 'receiver': receiver, 'sender': sender, 'link': link, 'site': site,
#                            'motivation': task_member.motivation})
#             text_content = render_to_string('task_member_applied.mail.txt', context_instance=ctx)
#             html_content = render_to_string('task_member_applied.mail.html', context_instance=ctx)
#             translation.deactivate()
#             msg = EmailMultiAlternatives(subject=subject, body=text_content, to=[receiver.email])
#             msg.attach_alternative(html_content, "text/html")
#             msg.send()
#
#
# @receiver(post_save, weak=False, sender=TASK_MEMBER_MODEL)
# def accepted_member_notification(sender, instance, created, **kwargs):
#     """
#     Signal handler for existing members status changes. When a task member is
#     accepted or refused by the task author/manager, an email will be sent to
#     inform the member by this function.
#     """
#     if not created:
#         task_member = instance
#
#         if task_member.task_id:
#             task = TASK_MODEL.objects.get(pk=task_member.task_id)
#
#             site = 'https://' + Site.objects.get_current().domain
#
#             if task_member.status == TASK_MEMBER_MODEL.TaskMemberStatuses.accepted:
#                 sender = task.author
#                 receiver = task_member.member
#                 link = '/go/tasks/{0}'.format(task.id)
#
#                 # Compose the mail
#                 # Set the language for the receiver
#                 translation.activate(receiver.primary_language)
#                 subject = _('{sender} accepted you to complete the tasks you applied for.'.format(
#                     sender=sender.get_short_name()))
#                 context = Context({'task': task, 'receiver': receiver, 'sender': sender, 'link': link, 'site': site})
#                 text_content = get_template('task_member_accepted.mail.txt').render(context)
#                 html_content = get_template('task_member_accepted.mail.html').render(context)
#                 translation.deactivate()
#                 msg = EmailMultiAlternatives(subject=subject, body=text_content, to=[receiver.email])
#                 msg.attach_alternative(html_content, "text/html")
#                 msg.send()
#
#             if task_member.status == TASK_MEMBER_MODEL.TaskMemberStatuses.rejected:
#                 sender = task.author
#                 receiver = task_member.member
#                 link = '/go/tasks/{0}'.format(task.id)
#
#                 # Compose the mail
#                 # Set the language for the receiver
#                 translation.activate(receiver.primary_language)
#                 subject = _('{sender} found someone else to do the task you applied for.'.format(
#                     sender=sender.get_short_name()))
#                 context = Context({'task': task, 'receiver': receiver, 'sender': sender, 'link': link, 'site': site})
#                 text_content = get_template('task_member_rejected.mail.txt').render(context)
#                 html_content = get_template('task_member_rejected.mail.html').render(context)
#                 translation.deactivate()
#                 msg = EmailMultiAlternatives(subject=subject, body=text_content, to=[receiver.email])
#                 msg.attach_alternative(html_content, "text/html")
#                 msg.send()
#
#
# @receiver(post_save, weak=False, sender=TASK_MODEL)
# def send_mail_task_realized(sender, instance, created, **kwargs):
#     """
#     Send (multiple) e-mails when a task is realized.
#     The task members that weren't rejected are the receivers.
#     """
#     if not created and instance.status == 'realized':
#         task = instance
#         mail_sender = task.author
#         link = '/go/tasks/{0}'.format(task.id)
#         site = 'https://' + Site.objects.get_current().domain
#
#         qs = task.members.exclude(status=TASK_MEMBER_MODEL.TaskMemberStatuses.rejected)
#         receivers = [taskmember.member for taskmember in qs]
#
#         emails = []
#
#         for receiver in receivers:
#             translation.activate(receiver.primary_language)
#             subject = _('Good job! "{task}" is realized!.'.format(task=task.title))
#             context = Context({'task': task, 'receiver': receiver, 'sender': mail_sender, 'link': link, 'site': site})
#             text_content = get_template('task_realized.mail.txt').render(context)
#             html_content = get_template('task_realized.mail.html').render(context)
#             translation.deactivate()
#             msg = EmailMultiAlternatives(subject=subject, body=text_content, to=[receiver.email])
#             msg.attach_alternative(html_content, "text/html")
#             emails.append(msg)
#
#         if emails:
#             connection = get_connection()
#             connection.send_messages(emails)
#             connection.close()
