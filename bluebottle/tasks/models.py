import pytz
from datetime import datetime

from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.fields import (
    ModificationDateTimeField, CreationDateTimeField)
from djchoices.choices import DjangoChoices, ChoiceItem

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


class Task(models.Model):

    class TaskStatuses(DjangoChoices):
        open = ChoiceItem('open', label=_('Open'))
        in_progress = ChoiceItem('in progress', label=_('In progress'))
        closed = ChoiceItem('closed', label=_('Closed'))
        realized = ChoiceItem('realized', label=_('Realised'))

    class TaskTypes(DjangoChoices):
        ongoing = ChoiceItem('ongoing', label=_('Ongoing (with deadline)'))
        event = ChoiceItem('event', label=_('Event (on set date)'))

    title = models.CharField(_('title'), max_length=100)
    description = models.TextField(_('description'))
    location = models.CharField(_('location'), max_length=200, null=True,
                                blank=True)
    people_needed = models.PositiveIntegerField(_('people needed'), default=1)

    project = models.ForeignKey('projects.Project')
    # See Django docs on issues with related name and an (abstract) base class:
    # https://docs.djangoproject.com/en/dev/topics/db/models/#be-careful-with-related-name
    author = models.ForeignKey('members.Member',
                               related_name='%(app_label)s_%(class)s_related')
    status = models.CharField(_('status'), max_length=20,
                              choices=TaskStatuses.choices,
                              default=TaskStatuses.open)
    type = models.CharField(_('type'), max_length=20,
                            choices=TaskTypes.choices,
                            default=TaskTypes.ongoing)

    date_status_change = models.DateTimeField(_('date status change'),
                                              blank=True, null=True)

    deadline = models.DateTimeField(_('date'), help_text=_('Deadline or event date'))

    objects = models.Manager()

    # required resources
    time_needed = models.FloatField(
        _('time_needed'),
        help_text=_('Estimated number of hours needed to perform this task.'))

    skill = models.ForeignKey('tasks.Skill',
                              verbose_name=_('Skill needed'), null=True)

    # internal usage
    created = CreationDateTimeField(
        _('created'), help_text=_('When this task was created?'))
    updated = ModificationDateTimeField(_('updated'))

    class Meta:
        verbose_name = _(u'task')
        verbose_name_plural = _(u'task')

        ordering = ['-created']

    def __init__(self, *args, **kwargs):
        super(Task, self).__init__(*args, **kwargs)
        self._original_status = self.status

    def __unicode__(self):
        return self.title

    def set_in_progress(self):
        self.status = self.TaskStatuses.in_progress
        self.save()

    @property
    def people_applied(self):
        return self.members.count()

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

        # Ensure deadline time is set to the end of the day
        self.deadline = pytz.utc.localize(datetime.combine(self.deadline, datetime.max.time()))

        super(Task, self).save(*args, **kwargs)


class Skill(models.Model):
    name = models.CharField(_('english name'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    disabled = models.BooleanField(_('disabled'), default=False)

    @property
    def localized_name(self):
        return _(self.name)

    def __unicode__(self):
        return str(self.localized_name)

    class Meta:
        ordering = ('id',)


class TaskMember(models.Model):
    class TaskMemberStatuses(DjangoChoices):
        applied = ChoiceItem('applied', label=_('Applied'))
        accepted = ChoiceItem('accepted', label=_('Accepted'))
        rejected = ChoiceItem('rejected', label=_('Rejected'))
        stopped = ChoiceItem('stopped', label=_('Stopped'))
        realized = ChoiceItem('realized', label=_('Realised'))

    member = models.ForeignKey('members.Member',
                               related_name='%(app_label)s_%(class)s_related')
    task = models.ForeignKey('tasks.Task', related_name="members")
    status = models.CharField(_('status'), max_length=20,
                              choices=TaskMemberStatuses.choices,
                              default=TaskMemberStatuses.applied)
    motivation = models.TextField(
        _('Motivation'), help_text=_('Motivation by applicant.'), blank=True)
    comment = models.TextField(_('Comment'),
                               help_text=_('Comment by task owner.'),
                               blank=True)
    time_spent = models.PositiveSmallIntegerField(
        _('time spent'), default=0,
        help_text=_('Time spent executing this task.'))

    externals = models.PositiveSmallIntegerField(
        _('Externals'), default=0,
        help_text=_('External people helping for this task'))

    created = CreationDateTimeField(_('created'))
    updated = ModificationDateTimeField(_('updated'))

    _initial_status = None

    # objects = models.Manager()

    class Meta:
        verbose_name = _(u'task member')
        verbose_name_plural = _(u'task members')

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
    def time_applied_for(self):
        return self.task.time_needed

    @property
    def project(self):
        return self.task.project


class TaskFile(models.Model):
    author = models.ForeignKey('members.Member',
                               related_name='%(app_label)s_%(class)s_related')
    title = models.CharField(max_length=255)
    file = models.FileField(_('file'), upload_to='task_files/')
    created = CreationDateTimeField(_('created'))
    updated = ModificationDateTimeField(_('Updated'))
    task = models.ForeignKey('tasks.Task', related_name="files")

    class Meta:
        verbose_name = _(u'task file')
        verbose_name_plural = _(u'task files')


from .taskmail import *
from .taskwallmails import *
from .signals import *
