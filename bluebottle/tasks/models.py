from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.fields import (
    ModificationDateTimeField, CreationDateTimeField)
from djchoices.choices import DjangoChoices, ChoiceItem
from tenant_extras.utils import TenantLanguage

from bluebottle.bb_metrics.utils import bb_track
from bluebottle.clients import properties
from bluebottle.clients.utils import tenant_url
from bluebottle.utils.email_backend import send_mail
from bluebottle.utils.managers import UpdateSignalsQuerySet
from bluebottle.utils.utils import PreviousStatusMixin

GROUP_PERMS = {
    'Staff': {
        'perms': (
            'add_task', 'change_task', 'delete_task',
            'add_taskmember', 'change_taskmember', 'delete_taskmember',
        )
    }
}


class Task(models.Model, PreviousStatusMixin):

    class TaskStatuses(DjangoChoices):
        open = ChoiceItem('open', label=_('Open'))
        in_progress = ChoiceItem('in progress', label=_('Running'))
        realized = ChoiceItem('realized', label=_('Realised'))
        closed = ChoiceItem('closed', label=_('Closed'))

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

    objects = UpdateSignalsQuerySet.as_manager()

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
        verbose_name_plural = _(u'tasks')

        ordering = ['-created']

    class Analytics:
        type = 'task'
        tags = {
            'status': 'status',
            'location': 'project.location.name',
            'location_group': 'project.location.group.name',
            'theme': {
                'project.theme.name': {'translate': True}
            },
            'theme_slug': 'project.theme.slug'
        }
        fields = {
            'id': 'id',
            'user_id': 'author.id'
        }

    def __unicode__(self):
        return self.title

    def set_in_progress(self):
        self.status = self.TaskStatuses.in_progress
        self.save()

    def set_open(self):
        self.status = self.TaskStatuses.open
        self.save()

    def task_member_realized(self):
        # Called if a task member is realized. Now check if the other members 
        # are also realized and the deadline has expired. If so, then the task 
        # should also be realized. Members who are rejected, stopped, realized
        # withdrew or applied can be ignored as these are not seen as active members.
        if self.status == self.TaskStatuses.realized or self.deadline > timezone.now():
            return

        accepted_count = TaskMember.objects.filter(
            task=self,
            status__in=('accepted',)
        ).count()

        if accepted_count == 0:
            self.status = self.TaskStatuses.realized
            self.save()

    @property
    def members_applied(self):
        return self.members.exclude(status__in=['stopped', 'withdrew'])

    @property
    def people_applied(self):
        return self.members_applied.count()

    @property
    def people_accepted(self):
        members = self.members.filter(status__in=['accepted', 'realized'])
        total_externals = 0
        for member in members:
            total_externals += member.externals
        return members.count() + total_externals

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

        if self.status == 'in progress':
            self.status = 'realized'
        else:
            self.status = 'closed'
        self.save()

        data = {
            "Task": self.title,
            "Author": self.author.username
        }
        bb_track("Task Deadline Reached", data)

    def status_changed(self, oldstate, newstate):
        """ called by post_save signal handler, if status changed """
        # confirm everything with task owner

        if oldstate in ("in progress", "open", "closed") and newstate == "realized":
            self.project.check_task_status()

            with TenantLanguage(self.author.primary_language):
                subject = _("The status of your task '{0}' is set to realized").format(self.title)

            send_mail(
                template_name="tasks/mails/task_status_realized.mail",
                subject=subject,
                title=self.title,
                to=self.author,
                site=tenant_url(),
                link='/go/tasks/{0}'.format(self.id)
            )

        if oldstate in ("in progress", "open") and newstate == "closed":

            with TenantLanguage(self.author.primary_language):
                subject = _("The status of your task '{0}' is set to closed").format(self.title)

            send_mail(
                template_name="tasks/mails/task_status_closed.mail",
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
        previous_status = None
        if self.pk:
            try:
                previous_status = self.__class__.objects.get(pk=self.pk).status
            except self.__class__.DoesNotExist:
                pass

        if not self.author_id:
            self.author = self.project.owner

        super(Task, self).save(*args, **kwargs)

        # Only log task status if the status has changed
        if self is not None and previous_status != self.status:
            TaskStatusLog.objects.create(
                task=self, status=self.status)


class Skill(models.Model):
    name = models.CharField(_('english name'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    disabled = models.BooleanField(_('disabled'), default=False)

    @property
    def localized_name(self):
        return _(self.name)

    def __unicode__(self):
        return unicode(self.localized_name)

    class Meta:
        ordering = ('id',)


class TaskMember(models.Model, PreviousStatusMixin):
    class TaskMemberStatuses(DjangoChoices):
        applied = ChoiceItem('applied', label=_('Applied'))
        accepted = ChoiceItem('accepted', label=_('Accepted'))
        rejected = ChoiceItem('rejected', label=_('Rejected'))
        stopped = ChoiceItem('stopped', label=_('Stopped'))
        withdrew = ChoiceItem('withdrew', label=_('Withdrew'))
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

    objects = UpdateSignalsQuerySet.as_manager()

    class Meta:
        verbose_name = _(u'task member')
        verbose_name_plural = _(u'task members')

    class Analytics:
        type = 'task_member'
        tags = {
            'status': 'status',
            'location': 'task.project.location.name',
            'location_group': 'task.project.location.group.name',
            'theme': {
                'task.project.theme.name': {'translate': True}
            },
            'theme_slug': 'task.project.theme.slug'
        }
        fields = {
            'id': 'id',
            'hours': 'time_spent',
            'task_id': 'task.id',
            'user_id': 'member.id'
        }

    def save(self, *args, **kwargs):
        previous_status = None
        if self.pk:
            previous_status = self.__class__.objects.get(pk=self.pk).status

        super(TaskMember, self).save(*args, **kwargs)

        # Only log task member status if the status has changed
        if self is not None and previous_status != self.status:
            TaskMemberStatusLog.objects.create(
                task_member=self, status=self.status)

    def delete(self, using=None, keep_parents=False):
        super(TaskMember, self).delete(using=using, keep_parents=keep_parents)

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


class TaskStatusLog(models.Model):
    task = models.ForeignKey('tasks.Task')
    status = models.CharField(_('status'), max_length=20)
    start = CreationDateTimeField(
        _('created'), help_text=_('When this task entered in this status.'))


class TaskMemberStatusLog(models.Model):
    task_member = models.ForeignKey('tasks.TaskMember')
    status = models.CharField(_('status'), max_length=20)
    start = CreationDateTimeField(
        _('created'), help_text=_('When this task member entered in this status.'))


from .taskmail import *  # noqa
from .taskwallmails import *  # noqa
from .signals import *  # noqa
