from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.fields import (CreationDateTimeField,
                                         ModificationDateTimeField)

from bluebottle.utils.utils import StatusDefinition


class Reward(models.Model):
    """
    Rewards for donations
    """
    amount = models.DecimalField(_('Amount'), max_digits=16, decimal_places=2)
    title = models.CharField(_('Title'), max_length=30)
    description = models.CharField(_('Description'), max_length=200)
    project = models.ForeignKey('projects.Project', verbose_name=_('Project'))
    limit = models.IntegerField(_('Limit'), null=True, blank=True,
                                help_text=_('How many of this rewards are available'))

    created = CreationDateTimeField(_('creation date'))
    updated = ModificationDateTimeField(_('last modification'))

    @property
    def count(self):
        from bluebottle.donations.models import Donation
        return Donation.objects\
            .filter(project=self.project)\
            .filter(reward=self)\
            .filter(order__status__in=[StatusDefinition.PENDING, StatusDefinition.SUCCESS])\
            .count()

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['-project__created', 'amount']
        verbose_name = _("Gift")
        verbose_name_plural = _("Gifts")
