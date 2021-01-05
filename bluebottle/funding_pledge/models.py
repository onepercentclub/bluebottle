from __future__ import absolute_import
from builtins import object
from django.db import models
from django.utils.translation import ugettext_lazy as _

from bluebottle.funding.models import Payment, PaymentProvider, BankAccount


class PledgePayment(Payment):
    provider = 'pledge'

    def refund(self):
        pass


class PledgePaymentProvider(PaymentProvider):

    title = 'Pledges only'

    @property
    def payment_methods(self):
        return []

    class Meta(object):
        verbose_name = 'Pledge payment provider'


class PledgeBankAccount(BankAccount):
    provider_class = PledgePaymentProvider

    account_holder_name = models.CharField(
        _("Account holder name"), max_length=100, null=True, blank=True)
    account_holder_address = models.CharField(
        _("Account holder address"), max_length=255, null=True, blank=True)
    account_holder_postal_code = models.CharField(
        _("Account holder postal code"), max_length=20, null=True, blank=True)
    account_holder_city = models.CharField(
        _("Account holder city"), max_length=255, null=True, blank=True)
    account_holder_country = models.ForeignKey(
        'geo.Country',
        verbose_name=_('Account holder country'),
        blank=True, null=True,
        related_name="pledge_account_holder_country")

    account_number = models.CharField(
        _("Account number"),
        max_length=255, null=True, blank=True)
    account_details = models.CharField(
        _("Account details"),
        max_length=500, null=True, blank=True)
    account_bank_country = models.ForeignKey(
        'geo.Country',
        verbose_name=_('Account bank country'),
        blank=True, null=True,
        related_name="pledge_account_bank_country")

    def save(self, *args, **kwargs):
        super(PledgeBankAccount, self).save(*args, **kwargs)

    class Meta(object):
        verbose_name = _('Pledge bank account')
        verbose_name_plural = _('Pledge bank accounts')

    class JSONAPIMeta(object):
        resource_name = 'payout-accounts/pledge-external-accounts'

    def __str__(self):
        return u"Pledge bank account {}".format(self.account_holder_name)

from .states import *  # noqa
