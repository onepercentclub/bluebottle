from builtins import str
from builtins import object
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericRelation
from future.utils import python_2_unicode_compatible

from bluebottle.fsm.triggers import TriggerMixin

from polymorphic.models import PolymorphicModel

from bluebottle.files.fields import ImageField
from bluebottle.initiatives.models import Initiative
from bluebottle.follow.models import Follow
from bluebottle.utils.models import ValidatedModelMixin, AnonymizationMixin
from bluebottle.utils.utils import get_current_host, get_current_language, clean_html


@python_2_unicode_compatible
class Activity(TriggerMixin, AnonymizationMixin, ValidatedModelMixin, PolymorphicModel):
    owner = models.ForeignKey(
        'members.Member',
        verbose_name=_('owner'),
        related_name='activities',
    )

    highlight = models.BooleanField(default=False,
                                    help_text=_('Highlight this activity to show it on homepage'))

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)
    transition_date = models.DateTimeField(
        _('contribution date'),
        help_text=_('Date the contribution took place.'),
        null=True, blank=True
    )

    status = models.CharField(max_length=40)

    review_status = models.CharField(max_length=40, default='draft')

    initiative = models.ForeignKey(Initiative, related_name='activities')

    title = models.CharField(_('Title'), max_length=255)
    slug = models.SlugField(_('Slug'), max_length=100, default='new')
    description = models.TextField(
        _('Description'), blank=True
    )

    image = ImageField(blank=True, null=True)

    video_url = models.URLField(
        _('video'),
        max_length=100,
        blank=True,
        null=True,
        default='',
        help_text=_(
            "Do you have a video pitch or a short movie that "
            "explains your activity? Cool! We can't wait to see it! "
            "You can paste the link to YouTube or Vimeo video here"
        )
    )
    segments = models.ManyToManyField(
        'segments.segment',
        verbose_name=_('Segment'),
        related_name='activities',
        blank=True
    )

    followers = GenericRelation('follow.Follow', object_id_field='instance_id')
    messages = GenericRelation('notifications.Message')

    follows = GenericRelation(Follow, object_id_field='instance_id')
    wallposts = GenericRelation('wallposts.Wallpost', related_query_name='activity_wallposts')

    @property
    def stats(self):
        return {}

    class Meta(object):
        verbose_name = _("Activity")
        verbose_name_plural = _("Activities")
        permissions = (
            ('api_read_activity', 'Can view activity through the API'),
            ('api_read_own_activity', 'Can view own activity through the API'),
        )

    def __str__(self):
        return self.title or str(_('-empty-'))

    def save(self, **kwargs):
        if self.slug in ['', 'new']:
            if self.title and slugify(self.title):
                self.slug = slugify(self.title)
            else:
                self.slug = 'new'

        if not self.owner_id:
            self.owner = self.initiative.owner

        self.description = clean_html(self.description)

        super(Activity, self).save(**kwargs)

        if not self.segments.count():
            for segment in self.owner.segments.all():
                self.segments.add(segment)

    def get_absolute_url(self):
        domain = get_current_host()
        language = get_current_language()
        link = u"{}/{}/initiatives/activities/details/{}/{}/{}".format(
            domain, language,
            self.__class__.__name__.lower(),
            self.pk,
            self.slug
        )
        return link

    @property
    def organizer(self):
        return self.contributions.instance_of(Organizer).first()


def NON_POLYMORPHIC_CASCADE(collector, field, sub_objs, using):
    # This fixing deleting related polymorphic objects through admin
    return models.CASCADE(collector, field, sub_objs.non_polymorphic(), using)


@python_2_unicode_compatible
class Contribution(TriggerMixin, AnonymizationMixin, PolymorphicModel):
    status = models.CharField(max_length=40)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)
    transition_date = models.DateTimeField(null=True, blank=True)
    contribution_date = models.DateTimeField()

    activity = models.ForeignKey(Activity, related_name='contributions', on_delete=NON_POLYMORPHIC_CASCADE)
    user = models.ForeignKey('members.Member', verbose_name=_('user'), null=True, blank=True)

    @property
    def owner(self):
        return self.user

    @property
    def date(self):
        return self.activity.contribution_date

    def save(self, *args, **kwargs):
        if not self.contribution_date:
            self.contribution_date = self.date

        super(Contribution, self).save(*args, **kwargs)

    class Meta(object):
        ordering = ('-created',)

    def __str__(self):
        return str(_('Contribution'))


@python_2_unicode_compatible
class Organizer(Contribution):
    class Meta(object):
        verbose_name = _("Activity owner")
        verbose_name_plural = _("Activity owners")

    class JSONAPIMeta(object):
        resource_name = 'contributions/organizers'

    def save(self, *args, **kwargs):
        if not self.contribution_date:
            self.contribution_date = self.activity.created

        super(Organizer, self).save()

    def __str__(self):
        if self.user:
            return self.user.full_name
        else:
            return _('Activity owner')


from bluebottle.activities.signals import *  # noqa
from bluebottle.activities.wallposts import *  # noqa
from bluebottle.activities.states import *  # noqa
