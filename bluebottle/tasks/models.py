from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.timezone import now
from django.utils.translation import ugettext as _

from django_extensions.db.fields import (
    ModificationDateTimeField, CreationDateTimeField)
from djchoices.choices import DjangoChoices, ChoiceItem
from taggit_autocomplete_modified.managers import (
    TaggableManagerAutocomplete as TaggableManager)

from bluebottle.utils.utils import clean_for_hashtag
from bluebottle.projects import get_project_model

PROJECT_MODEL = get_project_model()


class Skill(models.Model):

    name = models.CharField(_("english name"), max_length=100, unique=True)
    name_nl = models.CharField(_("dutch name"), max_length=100, unique=True)
    description = models.TextField(_("description"), blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('id', )


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
            statuses.applied, statuses.accepted, statuses.realized] # NOTE: should applied be in here too?
        projects = PROJECT_MODEL.objects.filter(
            task__taskmember__member=user,
            task__taskmember__status__in=valid_statuses).distinct()
        return projects


class Task(models.Model):
    """ Tasks """

    class TaskStatuses(DjangoChoices):
        open = ChoiceItem('open', label=_("Open"))
        in_progress = ChoiceItem('in progress', label=_("In progress"))
        closed = ChoiceItem('closed', label=_("Closed"))
        realized = ChoiceItem('realized', label=_("Realised"))

    title = models.CharField(_("title"), max_length=100)
    description = models.TextField(_("description"))
    end_goal = models.TextField(_("end goal"))
    location = models.CharField(_("location"), max_length=200)

    expertise = models.CharField(_("old expertise"), max_length=200)
    skill = models.ForeignKey(Skill, verbose_name=_("Skill needed"), null=True)
    time_needed = models.CharField(
        _("time_needed"), max_length=200,
        help_text=_("Estimated number of hours needed to perform this task."))

    status = models.CharField(
        _("status"), max_length=20, choices=TaskStatuses.choices,
        default=TaskStatuses.open)
    date_status_change = models.DateTimeField(_("status since"), blank=True, null=True)

    people_needed = models.PositiveIntegerField(
        _("people needed"), default=1,
        help_text=_("How many people are needed for this task?"))

    project = models.ForeignKey(settings.PROJECTS_PROJECT_MODEL)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='author')
    created = CreationDateTimeField(
        _("created"), help_text=_("When this task was created?"))
    updated = ModificationDateTimeField(_("updated"))

    tags = TaggableManager(blank=True, verbose_name=_("tags"))

    deadline = models.DateTimeField()

    objects = models.Manager()
    supported_projects = SupportedProjectsManager()

    def __unicode__(self):
        return self.title

    def __init__(self, *args, **kwargs):
        super(Task, self).__init__(*args, **kwargs)
        self._original_status = self.status

    def get_meta_title(self, **kwargs):
        project = self.project
        country = project.country.name if project.country else ''
        return u"%(task_name)s | %(expertise)s | %(country)s" % {
            'task_name': self.title,
            'expertise': self.skill.name if self.skill else '',
            'country': country,
        }

    def get_fb_title(self, **kwargs):
        project = self.project
        country = project.country.name if project.country else ''
        return _(u"Share your skills: {task_name} in {country}").format(task_name=self.title, country=country)

    def get_tweet(self, **kwargs):
        project = self.project
        country = project.country.name if project.country else ''

        request = kwargs.get('request')
        if request:
            lang_code = request.LANGUAGE_CODE
        else:
            lang_code = 'en'
        twitter_handle = settings.TWITTER_HANDLES.get(lang_code, settings.DEFAULT_TWITTER_HANDLE)

        expertise = self.skill.name if self.skill else ''
        expertise_hashtag = clean_for_hashtag(expertise)

        tweet = _(u"Share your skills: {task_name} in {country} {{URL}}"
                  u" #{expertise} via @{twitter_handle}").format(
                      task_name=self.title,
                      country=country,
                      expertise=expertise_hashtag,
                      twitter_handle=twitter_handle)
        return tweet

    class Meta:
        ordering = ['-created']


class TaskMember(models.Model):

    class TaskMemberStatuses(DjangoChoices):
        applied = ChoiceItem('applied', label=_("Applied"))
        accepted = ChoiceItem('accepted', label=_("Accepted"))
        rejected = ChoiceItem('rejected', label=_("Rejected"))
        stopped = ChoiceItem('stopped', label=_("Stopped"))
        realized = ChoiceItem('realized', label=_("Realised"))

    task = models.ForeignKey('Task')
    member = models.ForeignKey(settings.AUTH_USER_MODEL)
    status = models.CharField(
        _("status"), max_length=20, choices=TaskMemberStatuses.choices)

    motivation = models.TextField(
        _("Motivation"), help_text=_("Motivation by applicant."), blank=True)
    comment = models.TextField(_("Comment"), help_text=_("Comment by task owner."), blank=True)
    time_spent = models.PositiveSmallIntegerField(
        _('"time spent'), default=0, help_text=_("Time spent executing this task."))

    created = CreationDateTimeField(_("created"))
    updated = ModificationDateTimeField(_("updated"))

    _initial_status = None

    def __init__(self, *args, **kwargs):
        super(TaskMember, self).__init__(*args, **kwargs)
        self._initial_status = self.status


class TaskFile(models.Model):

    task = models.ForeignKey('Task')
    author = models.ForeignKey(settings.AUTH_USER_MODEL)
    title = models.CharField(max_length=255)
    file = models.FileField(_("file"), upload_to='task_files/')
    created = CreationDateTimeField(_("created"))
    updated = ModificationDateTimeField(_("Updated"))



### SIGNALS ###
@receiver(pre_save, weak=False, sender=Task, dispatch_uid="log-task-status")
def log_task_status(sender, instance, **kwargs):
    if instance.status != instance._original_status:
        instance.date_status_change = now()

@receiver(pre_save, weak=False, sender=TaskMember, dispatch_uid='set-hours-spent-taskmember')
def set_hours_spent_taskmember(sender, instance, **kwargs):
    if instance.status != instance._initial_status and instance.status == TaskMember.TaskMemberStatuses.realized:
        hours_spent = instance.task.time_needed
        if hours_spent > 8:
            hours_spent = 8
        instance.time_spent = hours_spent
