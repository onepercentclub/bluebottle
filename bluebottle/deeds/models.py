from django.db import models
from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.models import Activity


class Deed(Activity):

    start = models.DateField(blank=True, null=True)
    end = models.DateField(blank=True, null=True)

    auto_approve = True

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

    @property
    def required_fields(self):
        fields = ['title', 'description']
        return fields
