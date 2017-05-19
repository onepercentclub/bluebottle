from datetime import timedelta

from django.db import models, connection
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext, ugettext_lazy as _

from django_extensions.db.fields import (
    ModificationDateTimeField, CreationDateTimeField)
from djchoices.choices import DjangoChoices, ChoiceItem
from tenant_extras.utils import TenantLanguage

from bluebottle.bb_metrics.utils import bb_track
from bluebottle.clients import properties
from bluebottle.utils.managers import UpdateSignalsQuerySet
from bluebottle.utils.utils import PreviousStatusMixin


GROUP_PERMS = {
    'Staff': {
        'perms': (
            'add_task', 'change_task', 'delete_task',
            'add_taskmember', 'change_taskmember', 'delete_taskmember',
            'add_taskfile', 'change_taskfile', 'delete_taskfile',
            'add_skill', 'change_skill', 'delete_skill',
        )
    }
}


class Task(models.Model, PreviousStatusMixin):
    class TaskStatuses(DjangoChoices):
        open = ChoiceItem('open', label=_('Open'))
        full = ChoiceItem('full', label=_('Full'))
        in_progress = ChoiceItem('in progress', label=_('Running'))
        realized = ChoiceItem('realized', label=_('Realised'))
        closed = ChoiceItem('closed', label=_('Closed'))

    class TaskTypes(DjangoChoices):
        ongoing = ChoiceItem('ongoing', label=_('Ongoing (with deadline)'))
        event = ChoiceItem('event', label=_('Event (on set date)'))

    class TaskAcceptingChoices(DjangoChoices):
        manual = ChoiceItem('manual', label=_('Manual'))
        automatic = ChoiceItem('automatic', label=_('Automatic'))

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

    accepting = models.CharField(_('accepting'), max_length=20,
                                 choices=TaskAcceptingChoices.choices,
                                 default=TaskAcceptingChoices.manual)

    date_status_change = models.DateTimeField(_('date status change'),
                                              blank=True, null=True)

    deadline = models.DateTimeField(_('deadline'), help_text=_('Deadline or event date'))
    deadline_to_apply = models.DateTimeField(
        _('deadline_to_apply'), help_text=_('Deadline to apply')
    )

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

    def __unicode__(self):
        return self.title

    def set_in_progress(self):
        self.status = self.TaskStatuses.in_progress
        self.save()

    def set_full(self):
        self.status = self.TaskStatuses.full
        self.save()

    def set_open(self):
        self.status = self.TaskStatuses.open
        self.save()

    @property
    def expertise_based(self):
        return self.skill.expertise if self.skill else False

    @property
    def members_applied(self):
        return self.members.exclude(status__in=['stopped', 'withdrew'])

    @property
    def members_realized(self):
        return self.members.filter(status=self.TaskStatuses.realized)

    @property
    def externals_applied(self):
        total_externals = 0

        for member in self.members_applied:
            total_externals += member.externals
        return total_externals

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

    def deadline_to_apply_reached(self):
        with TenantLanguage(self.author.primary_language):
            subject = ugettext(
                "The deadline to apply for your task '{0}' has passed"
            ).format(self.title)

        send_deadline_to_apply_passed_mail(self, subject, connection.tenant)

        if self.status == self.TaskStatuses.open:
            if self.people_applied:
                if self.people_applied + self.externals_applied < self.people_needed:
                    self.people_needed = self.people_applied

                if self.type == self.TaskTypes.ongoing:
                    self.set_in_progress()
                else:
                    self.set_full()
            else:
                self.status = 'closed'

            self.save()

    def deadline_reached(self):
        if self.people_accepted:
            self.status = 'realized'
        else:
            self.status = 'closed'
        self.save()

    def members_changed(self):
        people_accepted = self.people_accepted

        if (self.status == self.TaskStatuses.open and
                self.people_needed <= people_accepted):
            if self.type == self.TaskTypes.ongoing:
                self.set_in_progress()
            else:
                self.set_full()

        if (self.status in (self.TaskStatuses.in_progress, self.TaskStatuses.full) and
                self.people_needed > people_accepted and
                self.deadline_to_apply > timezone.now()):
            self.set_open()

        if self.status == self.TaskStatuses.closed and self.members_realized:
            self.status = self.TaskStatuses.realized

        if self.status == self.TaskStatuses.realized and not self.members_realized:
            self.status = self.TaskStatuses.closed

        self.save()

    def status_changed(self, oldstate, newstate):
        """ called by post_save signal handler, if status changed """
        # confirm everything with task owner

        if oldstate in ("in progress", "open", "closed") and newstate == "realized":
            self.project.check_task_status()

            with TenantLanguage(self.author.primary_language):
                subject = ugettext("The status of your task '{0}' is set to realized").format(self.title)
                second_subject = ugettext("Don't forget to confirm the participants of your task!")
                third_subject = ugettext("Last chance to confirm the participants of your task")

            # Immediately send email about realized task
            send_task_realized_mail(self, 'task_status_realized', subject, connection.tenant)

            if getattr(settings, 'CELERY_RESULT_BACKEND', None):
                #  And schedule two more mails (in  3 and 6 days)
                send_task_realized_mail.apply_async(
                    [self, 'task_status_realized_reminder', second_subject, connection.tenant],
                    eta=timezone.now() + timedelta(minutes=settings.REMINDER_MAIL_DELAY)
                )
                send_task_realized_mail.apply_async(
                    [self, 'task_status_realized_second_reminder', third_subject, connection.tenant],
                    eta=timezone.now() + timedelta(minutes=2 * settings.REMINDER_MAIL_DELAY)
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


class Skill(models.Model):
    name = models.CharField(_('english name'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    expertise = models.BooleanField(_('expertise'),
                                    help_text=_('Is this skill expertise based, or could anyone do it?'),
                                    default=True)
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

    def delete(self, using=None, keep_parents=False):
        super(TaskMember, self).delete(using=using, keep_parents=keep_parents)

    @property
    def time_applied_for(self):
        return self.task.time_needed

    @property
    def project(self):
        return self.task.project

    def save(self, *args, **kwargs):
        if (self.status == self.TaskMemberStatuses.applied and
                self.task.accepting == self.task.TaskAcceptingChoices.automatic):
            self.status = self.TaskMemberStatuses.accepted

        super(TaskMember, self).save(*args, **kwargs)


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

    class Analytics:
        type = 'task'
        tags = {
            'id': 'task.id',
            'status': 'status',
            'theme': {
                'task.project.theme.name': {'translate': True}
            },
            'theme_slug': 'task.project.theme.slug',
            'location': 'task.project.location.name',
            'location_group': 'task.project.location.group.name',
            'country': 'task.project.country_name'
        }
        fields = {
            'id': 'task.id',
            'project_id': 'task.project.id',
            'user_id': 'task.author.id',
        }

        @staticmethod
        def timestamp(obj, created):
            return obj.start


class TaskMemberStatusLog(models.Model):
    task_member = models.ForeignKey('tasks.TaskMember')
    status = models.CharField(_('status'), max_length=20)
    start = CreationDateTimeField(
        _('created'), help_text=_('When this task member entered in this status.'))

    class Analytics:
        type = 'task_member'
        tags = {
            'id': 'task_member.id',
            'status': 'status',
            'location': 'task_member.project.location.name',
            'location_group': 'task_member.project.location.group.name',
            'country': 'task_member.project.country_name',
            'theme': {
                'task_member.project.theme.name': {'translate': True}
            },
            'theme_slug': 'task_member.project.theme.slug',
        }
        fields = {
            'id': 'task_member.id',
            'task_id': 'task_member.task.id',
            'project_id': 'task_member.project.id',
            'user_id': 'task_member.member.id',
        }

        @staticmethod
        def extra_fields(obj, created):
            # Force the time_spent to an int.
            return {'hours': int(obj.task_member.time_spent)}

        @staticmethod
        def timestamp(obj, created):
            return obj.start


from .taskmail import send_task_realized_mail, send_deadline_to_apply_passed_mail  # noqa
from .taskwallmails import *  # noqa
from .signals import *  # noqa
