from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.fields import (
    ModificationDateTimeField, CreationDateTimeField)
from djchoices.choices import DjangoChoices, ChoiceItem


class BaseSkill(models.Model):
    name = models.CharField(_('english name'), max_length=100, unique=True)
    name_nl = models.CharField(_('dutch name'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('id',)
        abstract = True


class BaseTaskMember(models.Model):
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
        abstract = True
        verbose_name = _(u'task member')
        verbose_name_plural = _(u'task members')


class BaseTaskFile(models.Model):
    author = models.ForeignKey('members.Member',
                               related_name='%(app_label)s_%(class)s_related')
    title = models.CharField(max_length=255)
    file = models.FileField(_('file'), upload_to='task_files/')
    created = CreationDateTimeField(_('created'))
    updated = ModificationDateTimeField(_('Updated'))
    task = models.ForeignKey('tasks.Task', related_name="files")

    class Meta:
        abstract = True
        verbose_name = _(u'task file')
        verbose_name_plural = _(u'task files')
