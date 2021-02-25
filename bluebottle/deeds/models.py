from django.db import models
from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.models import Activity, Contributor
from bluebottle.deeds.validators import EndDateValidator


class Deed(Activity):

    start = models.DateField(blank=True, null=True)
    end = models.DateField(blank=True, null=True)

    auto_approve = True

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
        fields = ['title', 'description']
        return fields

    @property
    def participants(self):
        return self.contributors.instance_of(DeedParticipant).filter(status='accepted')


class DeedParticipant(Contributor):
    class Meta(object):
        verbose_name = _("Participant")
        verbose_name_plural = _("Participants")

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
        resource_name = 'contributors/deeds/participant'
