from django.db import models
from django.db.models import SET_NULL

from django.utils.translation import gettext_lazy as _
from parler.models import TranslatedFields

from bluebottle.activities.models import Activity, Contributor, EffortContribution
from bluebottle.deeds.validators import EndDateValidator
from bluebottle.geo.models import Geolocation
from bluebottle.utils.models import SortableTranslatableModel


class CollectType(SortableTranslatableModel):
    disabled = models.BooleanField(default=False)

    translations = TranslatedFields(
        name=models.CharField(_('name'), max_length=100),
        description=models.TextField(_('description'), blank=True)
    )

    def __str__(self):
        return self.name

    class Meta(object):
        verbose_name = _('collect type')
        verbose_name_plural = _('collect types')
        permissions = (
            ('api_read_collecttype', 'Can view collect type through API'),
        )


class CollectActivity(Activity):

    start = models.DateField(blank=True, null=True)
    end = models.DateField(blank=True, null=True)

    type = models.ForeignKey(CollectType, null=True, blank=True, on_delete=SET_NULL)

    location = models.ForeignKey(Geolocation, null=True, blank=True, on_delete=SET_NULL)

    auto_approve = True

    @property
    def activity_date(self):
        return self.start

    class Meta(object):
        verbose_name = _("Collect Activity")
        verbose_name_plural = _("Collect Activities")
        permissions = (
            ('api_read_collect', 'Can view collect activity through the API'),
            ('api_add_collect', 'Can add collect activity through the API'),
            ('api_change_collect', 'Can change collect activity through the API'),
            ('api_delete_collect', 'Can delete collect activity through the API'),

            ('api_read_own_collect', 'Can view own collect activity through the API'),
            ('api_add_own_collect', 'Can add own collect activity through the API'),
            ('api_change_own_collect', 'Can change own collect activity through the API'),
            ('api_delete_own_collect', 'Can delete own collect activity through the API'),
        )

    validators = [EndDateValidator]

    class JSONAPIMeta(object):
        resource_name = 'activities/collects'

    @property
    def accepted_contributors(self):
        return self.contributors.instance_of(CollectContributor).filter(
            status__in=('accepted', 'succeeded', )
        )

    @property
    def required_fields(self):
        return super().required_fields + ['title', 'description']

    @property
    def efforts(self):
        return EffortContribution.objects.filter(
            contributor__activity=self,
            contribution_type='collect'
        )


class CollectContributor(Contributor):

    value = models.DecimalField(null=True, blank=True, decimal_places=5, max_digits=12)

    class Meta(object):
        verbose_name = _("Collect contributor")
        verbose_name_plural = _("Collect contributors")

        permissions = (
            ('api_read_collectcontributor', 'Can view collect contributor through the API'),
            ('api_add_collectcontributor', 'Can add collect contributor  through the API'),
            ('api_change_collectcontributor', 'Can change collect contributor  through the API'),
            ('api_delete_collectcontributor', 'Can delete collect contributor  through the API'),

            ('api_read_own_collectcontributor', 'Can view own collect contributor through the API'),
            ('api_add_own_collectcontributor', 'Can add own collect contributor through the API'),
            ('api_change_own_collectcontributor', 'Can change own collect contributor through the API'),
            ('api_delete_own_collectcontributor', 'Can delete own collect contributor through the API'),
        )

    class JSONAPIMeta(object):
        resource_name = 'contributors/collect/contributors'
