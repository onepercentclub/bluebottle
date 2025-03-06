import datetime
from urllib.parse import urlencode

from django.contrib.contenttypes.models import ContentType
from django.db import models, connection
from django.utils.translation import gettext_lazy as _

from bluebottle.activities.models import Activity, Contributor, EffortContribution
from bluebottle.activities.models import Organizer
from bluebottle.deeds.validators import EndDateValidator


class Deed(Activity):

    start = models.DateField(blank=True, null=True)
    end = models.DateField(blank=True, null=True)

    enable_impact = models.BooleanField(default=False)

    target = models.IntegerField(
        blank=True, null=True,
        help_text=_('The number of users you want to participate.')
    )

    auto_approve = True

    activity_type = _('Deed')

    @property
    def activity_date(self):
        return self.start

    class Meta(object):
        verbose_name = _("Deed")
        verbose_name_plural = _("Deeds")
        permissions = (
            ('api_read_deed', 'Can view deed through the API'),
            ('api_add_deed', 'Can add deed through the API'),
            ('api_change_deed', 'Can change deed through the API'),
            ('api_delete_deed', 'Can delete deed through the API'),

            ('api_read_own_deed', 'Can view own deed through the API'),
            ('api_add_own_deed', 'Can add own deed through the API'),
            ('api_change_own_deed', 'Can change own deed through the API'),
            ('api_delete_own_deed', 'Can delete own deed through the API'),
        )

    class JSONAPIMeta(object):
        resource_name = 'activities/deeds'

    validators = [EndDateValidator]

    @property
    def required_fields(self):
        fields = super().required_fields + ['title', 'description.html']

        if self.enable_impact:
            fields = fields + ['goals', 'target']

        return fields

    @property
    def uid(self):
        return '{}-collect-{}'.format(connection.tenant.client_name, self.pk)

    @property
    def google_calendar_link(self):
        details = self.description.html
        end = self.end + datetime.timedelta(days=1)
        dates = "{}/{}".format(self.start.strftime('%Y%m%d'), end.strftime('%Y%m%d'))

        url = u'https://calendar.google.com/calendar/render'
        params = {
            'action': u'TEMPLATE',
            'text': self.title,
            'dates': dates,
            'details': details,
            'uid': self.uid,
        }

        return u'{}?{}'.format(url, urlencode(params))

    @property
    def participants(self):
        if self.pk:
            return self.contributors.instance_of(DeedParticipant).filter(
                status__in=('accepted', 'succeeded', )
            )
        else:
            return []

    @property
    def succeeded_contributor_count(self):
        if self.pk:
            return self.participants.count() + self.deleted_successful_contributors
        else:
            return []

    @property
    def efforts(self):
        if self.pk:
            return EffortContribution.objects.filter(
                contributor__activity=self,
                contribution_type='deed'
            )
        else:
            return []

    @property
    def realized(self):
        if self.pk:
            return len(
                EffortContribution.objects.exclude(
                    contributor__polymorphic_ctype=ContentType.objects.get_for_model(Organizer)
                ).filter(
                    contributor__activity=self,
                    status__in=['succeeded', 'new', ]
                )
            )
        else:
            return []


class DeedParticipant(Contributor):
    class Meta(object):
        verbose_name = _("Deed participant")
        verbose_name_plural = _("Deed participants")

        permissions = (
            ('api_read_deedparticipant', 'Can view deed through the API'),
            ('api_add_deedparticipant', 'Can add deed through the API'),
            ('api_change_deedparticipant', 'Can change deed through the API'),
            ('api_delete_deedparticipant', 'Can delete deed through the API'),

            ('api_read_own_deedparticipant', 'Can view own deed through the API'),
            ('api_add_own_deedparticipant', 'Can add own deed through the API'),
            ('api_change_own_deedparticipant', 'Can change own deed through the API'),
            ('api_delete_own_deedparticipant', 'Can delete own deed through the API'),
        )

    class JSONAPIMeta(object):
        resource_name = 'contributors/deeds/participants'


from bluebottle.deeds.periodic_tasks import *  # noqa
