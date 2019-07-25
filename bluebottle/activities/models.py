from django.db import models
from django.template.defaultfilters import slugify
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericRelation

from bluebottle.fsm import FSMField, TransitionsMixin

from polymorphic.models import PolymorphicModel
from bluebottle.initiatives.models import Initiative
from bluebottle.activities.transitions import ActivityTransitions, ContributionTransitions
from bluebottle.utils.utils import get_current_host, get_current_language


class Activity(TransitionsMixin, PolymorphicModel):
    owner = models.ForeignKey(
        'members.Member',
        verbose_name=_('owner'),
        related_name='activities',
    )

    highlight = models.BooleanField(default=False,
                                    help_text=_('Highlight this activity to show it on homepage'))

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    status = FSMField(
        default=ActivityTransitions.values.draft
    )

    initiative = models.ForeignKey(Initiative, related_name='activities')

    title = models.CharField(_('title'), max_length=255)
    slug = models.SlugField(_('slug'), max_length=100, default='new')
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

    @property
    def contribution_count(self):
        return self.contributions.count()

    def save(self, **kwargs):
        if not self.slug or self.slug in ['new', ''] and self.title:
            self.slug = slugify(self.title)

        if not self.owner_id:
            self.owner = self.initiative.owner

        super(Activity, self).save(**kwargs)

    def get_absolute_url(self):
        domain = get_current_host()
        language = get_current_language()
        link = format_html("{}/{}/initiatives/activities/{}/{}/{}",
                           domain, language,
                           self.__class__.__name__.lower(), self.pk, self.slug)
        return link


class Contribution(TransitionsMixin, PolymorphicModel):
    status = FSMField(
        default=ContributionTransitions.values.new,
    )

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    activity = models.ForeignKey(Activity, related_name='contributions')
    user = models.ForeignKey('members.Member', verbose_name=_('user'), null=True)

    @property
    def owner(self):
        return self.user
