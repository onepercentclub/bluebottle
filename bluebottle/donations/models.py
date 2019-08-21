from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.fields import (ModificationDateTimeField,
                                         CreationDateTimeField)

from bluebottle.utils.fields import MoneyField
from bluebottle.utils.models import MailLog
from bluebottle.utils.utils import StatusDefinition


class Donation(models.Model):
    """
    Donation of an amount from a user to a project.
    """
    amount = MoneyField(_("Amount"))
    payout_amount = MoneyField(_("Payout amount"))

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
                               on_delete=models.SET_NULL,
                               null=True, blank=True)

    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))
    completed = models.DateTimeField(_("Ready"), blank=True, editable=False, null=True)
    anonymous = models.BooleanField(_("Anonymous"), default=False)
    name = models.CharField(_("Name of donor"), max_length=200, blank=True, null=True, db_index=True)

    mail_logs = GenericRelation(MailLog)

    class Meta:
        verbose_name = _('donation')
        verbose_name_plural = _('donations')

    @property
    def status(self):
        return self.order.status

    @property
    def user(self):
        return self.order.user

    @property
    def public_name(self):
        if not self.anonymous:
            return self.name

    @property
    def public_user(self):
        if self.anonymous or self.name:
            return None
        return self.user

    def __unicode__(self):
        return u'{} for {}'.format(self.amount, self.project)

    def get_payment_method(self):
        order_payment = self.order.get_latest_order_payment()
        if not order_payment:
            return '?'
        if order_payment.status == StatusDefinition.PLEDGED:
            return 'pledge'
        if not hasattr(order_payment, 'payment'):
            return '?'
        return order_payment.payment.method_name

    def save(self, *args, **kwargs):
        if not self.payout_amount or self.payout_amount.currency == self.amount.currency:
            self.payout_amount = self.amount
        super(Donation, self).save(*args, **kwargs)
