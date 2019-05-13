from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django_fsm import FSMField
from djchoices.choices import DjangoChoices, ChoiceItem
from polymorphic.models import PolymorphicModel
from sorl.thumbnail import ImageField

from bluebottle.initiatives.models import Initiative


class Activity(PolymorphicModel):
    class Status(DjangoChoices):
        open = ChoiceItem('open', _('open'))
        full = ChoiceItem('full', _('full'))
        running = ChoiceItem('running', _('running'))
        done = ChoiceItem('done', _('done'))
        closed = ChoiceItem('closed', _('closed'))

    owner = models.ForeignKey(
        'members.Member',
        verbose_name=_('owner'),
        related_name='own_%(class)s',
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    status = FSMField(
        default=Status.open,
        choices=Status.choices,
        protected=True
    )

    initiative = models.ForeignKey('initiatives.Initiative', related_name='activites')

    title = models.CharField(_('title'), max_length=255, unique=True, db_index=True)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    description = models.TextField(
        _('description'), blank=True
    )

    image = ImageField(
        _('image'),
        max_length=255,
        blank=True,
        upload_to='activity_images/',
        help_text=_('Main activity picture')
    )
    video_url = models.URLField(
        _('video'),
        max_length=100,
        blank=True,
        null=True,
        default='',
    )

    class Meta:
        verbose_name = _("Activity")
        verbose_name_plural = _("Activities")
        permissions = (
            ('api_read_activity', 'Can view activity through the API'),
            ('api_read_own_activity', 'Can view own activity through the API'),
        )

    def __unicode__(self):
        return self.title

    @property
    def contribution_count(self):
        return self.contributions.count()

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        super(Activity, self).save(**kwargs)

    @classmethod
    def initiative_is_approved(cls, instance):
        if not instance.id:
            return True
        return Initiative.is_approved(instance.initiative)


class Contribution(models.Model):
    class Status(DjangoChoices):
        new = ChoiceItem('new', _('new'))
        success = ChoiceItem('success', _('success'))
        failed = ChoiceItem('success', _('success'))

    status = FSMField(
        default=Status.new,
        protected=True
    )

    activity = models.ForeignKey(Activity, related_name='contributions')
    user = models.ForeignKey('members.Member', verbose_name=_('user'), null=True)
