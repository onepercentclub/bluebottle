from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.fields import GenericRelation

from bluebottle.fsm import FSMField

from djchoices.choices import DjangoChoices, ChoiceItem

from polymorphic.models import PolymorphicModel
from bluebottle.initiatives.models import Initiative


class Activity(PolymorphicModel):
    class Status(DjangoChoices):
        draft = ChoiceItem('draft', _('draft'))
        open = ChoiceItem('open', _('open'))
        full = ChoiceItem('full', _('full'))
        running = ChoiceItem('running', _('running'))
        done = ChoiceItem('done', _('done'))
        closed = ChoiceItem('closed', _('closed'))

    owner = models.ForeignKey(
        'members.Member',
        verbose_name=_('owner'),
        related_name='activities',
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    status = FSMField(
        default=Status.draft,
        choices=Status.choices,
    )
    initiative = models.ForeignKey(Initiative, related_name='activities')

    title = models.CharField(_('title'), max_length=255)
    slug = models.SlugField(_('slug'), max_length=100)
    description = models.TextField(
        _('description'), blank=True
    )

    followers = GenericRelation('follow.Follow', object_id_field='instance_id')

    class Meta:
        verbose_name = _("Activity")
        verbose_name_plural = _("Activities")
        permissions = (
            ('api_read_activity', 'Can view activity through the API'),
            ('api_read_own_activity', 'Can view own activity through the API'),
        )

    def __unicode__(self):
        return self.title

    def is_complete(self):
        return self.initiative.status == Initiative.Status.approved

    @property
    def contribution_count(self):
        return self.contributions.count()

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        super(Activity, self).save(**kwargs)

    @status.transition(
        source=Status.draft,
        target=Status.open,
        conditions=[is_complete]
    )
    def open(self):
        pass


class Contribution(PolymorphicModel):
    class Status(DjangoChoices):
        new = ChoiceItem('new', _('new'))
        success = ChoiceItem('success', _('success'))
        failed = ChoiceItem('success', _('success'))

    status = FSMField(
        default=Status.new,
        protected=True
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    activity = models.ForeignKey(Activity, related_name='contributions')
    user = models.ForeignKey('members.Member', verbose_name=_('user'), null=True)

    @classmethod
    def is_user(cls, instance, user):
        return instance.user == user

    @classmethod
    def is_activity_manager(cls, instance, user):
        return instance.activity.initiative.activity_manager == user
