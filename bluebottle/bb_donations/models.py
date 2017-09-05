from django.db import models
from django.utils.translation import ugettext as _

from django_extensions.db.fields import (ModificationDateTimeField,
                                         CreationDateTimeField)

from bluebottle.utils.fields import MoneyField


class BaseDonation(models.Model):
    """
    Donation of an amount from a user to a project.
    """
    amount = MoneyField(_("Amount"))

    project = models.ForeignKey('projects.Project',
                                verbose_name=_("Project"))
    fundraiser = models.ForeignKey('fundraisers.Fundraiser',
                                   verbose_name=_("Fundraiser"),
                                   null=True, blank=True)
    order = models.ForeignKey('orders.Order',
                              verbose_name=_("Order"),
                              related_name='donations',
                              null=True, blank=True)

    reward = models.ForeignKey('rewards.Reward',
                               verbose_name=_("Reward"),
                               related_name='donations',
                               null=True, blank=True)

    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))
    completed = models.DateTimeField(_("Ready"), blank=True, editable=False,
                                     null=True)

    anonymous = models.BooleanField(_("Anonymous"), default=False)

    @property
    def status(self):
        return self.order.status

    @property
    def user(self):
        return self.order.user

    @property
    def public_user(self):
        if self.anonymous:
            return None
        return self.user

    class Meta:
        abstract = True
