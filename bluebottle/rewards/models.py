from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.fields import (CreationDateTimeField,
                                         ModificationDateTimeField)

from bluebottle.donations.models import Donation
from bluebottle.utils.utils import StatusDefinition


class Reward(models.Model):
    """
    Rewards for donations
    """
    amount = models.DecimalField(_('Amount'), max_digits=16, decimal_places=2)
    title = models.CharField(_('Title'), max_length=30)
    description = models.CharField(_('Description'), max_length=200)
    project = models.ForeignKey(_('Project'), 'projects.Project')
    limit = models.Integerfield(_('Limit'), help_text=_('How many of this rewards are available'))

    creation_date = CreationDateTimeField(_('creation date'))
    modification_date = ModificationDateTimeField(_('last modification'))

    @property
    def count(self):
        return Donation.objects.filter(project=self.project).filter(
                status__in=[StatusDefinition.PENDING, StatusDefinition.SUCCESS]).count()

    def __unicode__(self):
        return self.title
