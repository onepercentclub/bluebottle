from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.fields import (CreationDateTimeField,
                                         ModificationDateTimeField)

from bluebottle.utils.fields import LegacyMoneyField as MoneyField
from bluebottle.utils.utils import StatusDefinition


class Reward(models.Model):
    """
    Rewards for donations
    """
    amount = MoneyField(_('Amount'))
    title = models.CharField(_('Title'), max_length=200)
    description = models.CharField(_('Description'), max_length=500)
    project = models.ForeignKey('projects.Project', verbose_name=_('Project'))
    limit = models.IntegerField(_('Limit'), null=True, blank=True,
                                help_text=_('How many of this rewards are available'))

    created = CreationDateTimeField(_('creation date'))
    updated = ModificationDateTimeField(_('last modification'))

    @property
    def owner(self):
        return self.project.owner

    @property
    def parent(self):
        return self.project

    @property
    def count(self):
        return self.donations.exclude(
            order__status=StatusDefinition.FAILED
        ).count()

    @property
    def success_count(self):
        return self.donations.filter(
            order__status__in=[StatusDefinition.PENDING, StatusDefinition.SUCCESS]
        ).count()

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['-project__created', 'amount']
        verbose_name = _("Gift")
        verbose_name_plural = _("Gifts")
        permissions = (
            ('api_read_reward', 'Can view reward through the API'),
            ('api_add_reward', 'Can add reward through the API'),
            ('api_change_reward', 'Can change reward through the API'),
            ('api_delete_reward', 'Can delete reward through the API'),

            ('api_read_own_reward', 'Can view own reward through the API'),
            ('api_add_own_reward', 'Can add own reward through the API'),
            ('api_change_own_reward', 'Can change own reward through the API'),
            ('api_delete_own_reward', 'Can delete own reward through the API'),

        )

    def delete(self, using=None, keep_parents=False):
        if self.success_count:
            raise ValueError(_('Not allowed to delete a reward with successful donations.'))
        return super(Reward, self).delete(using=using, keep_parents=False)
