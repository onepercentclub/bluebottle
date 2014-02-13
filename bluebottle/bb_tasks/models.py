from django.conf import settings
from django.db import models
import django.db.models.options as options
from django.utils.translation import ugettext as _

from django_extensions.db.fields import (
    ModificationDateTimeField, CreationDateTimeField)
from djchoices.choices import DjangoChoices, ChoiceItem
from taggit_autocomplete_modified.managers import TaggableManagerAutocomplete as TaggableManager

#from bluebottle.bb_projects import get_project_model

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('default_serializer',)

#PROJECT_MODEL = get_project_model()


class Skill(models.Model):

    name = models.CharField(_('english name'), max_length=100, unique=True)
    name_nl = models.CharField(_('dutch name'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('id', )


class TaskMember(models.Model):
    class TaskMemberStatuses(DjangoChoices):
        applied = ChoiceItem('applied', label=_('Applied'))
        accepted = ChoiceItem('accepted', label=_('Accepted'))
        rejected = ChoiceItem('rejected', label=_('Rejected'))
        stopped = ChoiceItem('stopped', label=_('Stopped'))
        realized = ChoiceItem('realized', label=_('Realised'))

    member = models.ForeignKey(settings.AUTH_USER_MODEL)
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
        super(TaskMember, self).__init__(*args, **kwargs)
        self._initial_status = self.status


class TaskFile(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL)
    title = models.CharField(max_length=255)
    file = models.FileField(_('file'), upload_to='task_files/')
    created = CreationDateTimeField(_('created'))
    updated = ModificationDateTimeField(_('Updated'))


class BaseTask(models.Model):
    """ The base Task model """

    class TaskStatuses(DjangoChoices):
        open = ChoiceItem('open', label=_('Open'))
        in_progress = ChoiceItem('in progress', label=_('In progress'))
        closed = ChoiceItem('closed', label=_('Closed'))
        realized = ChoiceItem('realized', label=_('Completed'))

    title = models.CharField(_('title'), max_length=100)
    description = models.TextField(_('description'))

    members = models.ManyToManyField(TaskMember, null=True)
    files = models.ManyToManyField(TaskFile, null=True)

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
    skill = models.ForeignKey(Skill, verbose_name=_('Skill needed'), null=True)

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
        statuses = TaskMember.TaskMemberStatuses

        valid_statuses = [
            statuses.applied, statuses.accepted, statuses.realized]
        projects = PROJECT_MODEL.objects.filter(
            task__taskmember__member=user,
            task__taskmember__status__in=valid_statuses).distinct()

        return projects
