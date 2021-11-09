from datetime import timedelta
from urllib.parse import urlencode

from django.db import models, connection
from django.db.models import SET_NULL

from django.utils.translation import gettext_lazy as _
from parler.models import TranslatedFields

from bluebottle.activities.models import Activity, Contributor, Contribution
from bluebottle.deeds.validators import EndDateValidator
from bluebottle.geo.models import Geolocation
from bluebottle.utils.models import SortableTranslatableModel


class CollectType(SortableTranslatableModel):
    disabled = models.BooleanField(default=False)

    translations = TranslatedFields(
        name=models.CharField(_('name'), max_length=100),
        unit=models.CharField(_('unit'), blank=True, max_length=100),
        unit_plural=models.CharField(_('unit plural'), blank=True, max_length=100)
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
    location_hint = models.TextField(_('location hint'), null=True, blank=True)

    target = models.DecimalField(decimal_places=3, max_digits=15, null=True, blank=True)
    realized = models.DecimalField(decimal_places=3, max_digits=15, null=True, blank=True)

    enable_impact = models.BooleanField(default=False)

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
    def uid(self):
        return '{}-collect-{}'.format(connection.tenant.client_name, self.pk)

    @property
    def google_calendar_link(self):

        details = self.description
        details += _('\nCollecting {type}').format(type=self.type)

        end = self.end + timedelta(days=1)
        dates = "{}/{}".format(self.start.strftime('%Y%m%d'), end.strftime('%Y%m%d'))

        url = u'https://calendar.google.com/calendar/render'
        params = {
            'action': u'TEMPLATE',
            'text': self.title,
            'dates': dates,
            'details': details,
            'uid': self.uid,
        }

        if self.location:
            params['location'] = self.location.formatted_address

        return u'{}?{}'.format(url, urlencode(params))

    @property
    def active_contributors(self):
        return self.contributors.instance_of(CollectContributor).filter(
            status='succeeded'
        )

    @property
    def required_fields(self):
        return super().required_fields + ['title', 'description', 'type']


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


class CollectContribution(Contribution):
    value = models.DecimalField(null=True, blank=True, decimal_places=5, max_digits=12)

    def save(self, *args, **kwargs):
        self.value = self.contributor.value

        super().save(*args, **kwargs)

    class Meta(object):
        verbose_name = _("Collect contribution")
        verbose_name_plural = _("Collect contributions")

    class JSONAPIMeta(object):
        resource_name = 'contributors/collect/contributions'
