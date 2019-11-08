from django.db import models
from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm import TransitionManager
from bluebottle.funding.models import Payment, PaymentProvider, BankAccount
from bluebottle.funding_pledge.transitions import PledgePaymentTransitions


class PledgePayment(Payment):
    provider = 'pledge'
    transitions = TransitionManager(PledgePaymentTransitions, 'status')


class PledgePaymentProvider(PaymentProvider):
    @property
    def payment_methods(self):
        return []

    class Meta:
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

    class Meta:
        verbose_name = _('Pledge bank account')
        verbose_name_plural = _('Pledge bank accounts')

    class JSONAPIMeta:
        resource_name = 'payout-accounts/pledge-external-accounts'
