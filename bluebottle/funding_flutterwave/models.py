from django.db import models
from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm import TransitionManager
from bluebottle.funding.models import Payment, PaymentProvider, PaymentMethod, BankAccount
from bluebottle.funding.transitions import PaymentTransitions


class FlutterwavePayment(Payment):
    tx_ref = models.CharField(max_length=30)

    transitions = TransitionManager(PaymentTransitions, 'status')


class FlutterwavePaymentProvider(PaymentProvider):

    pub_key = models.CharField(max_length=100)
    sec_key = models.CharField(max_length=100)
    prefix = models.CharField(max_length=100, default='goodup')

    @property
    def payment_methods(self):
        return [
            PaymentMethod(
                provider='flutterwave',
                name='Credit card',
                code='credit_card',
                currencies=['NGN'],
            )
        ]

    @property
    def private_settings(self):
        return {
            'sec_key': self.sec_key
        }

    @property
    def public_settings(self):
        return {
            'pub_key': self.pub_key,
            'prefix': self.prefix
        }

    class Meta:
        verbose_name = 'Flutterwave payment provider'


class FlutterwaveBankAccount(BankAccount):

    BANK_CHOICES = (
        ("", "Select bank"),
        ("044", "Access Bank"),
        ("063", "Access Bank PLC (Diamond)"),
        ("023", "Citi Bank"),
        ("050", "EcoBank PLC"),
        ("070", "Fidelity Bank"),
        ("608", "FINATRUST MICROFINANCE BANK"),
        ("011", "First Bank PLC"),
        ("214", "First City Monument Bank"),
        ("058", "Guaranty Trust Bank"),
        ("030", "Heritage Bank"),
        ("090175", "Highstreet Microfinance Bank"),
        ("301", "Jaiz Bank"),
        ("082", "Keystone Bank"),
        ("090267", "Kudimoney MF Bank"),
        ("076", "Polaris bank"),
        ("101", "ProvidusBank PLC"),
        ("221", "Stanbic IBTC Bank"),
        ("068", "Standard Chaterted bank PLC"),
        ("232", "Sterling Bank PLC"),
        ("100", "Suntrust Bank"),
        ("032", "Union Bank PLC"),
        ("033", "United Bank for Africa"),
        ("215", "Unity Bank PLC"),
        ("035", "Wema Bank PLC"),
        ("057", "Zenith bank PLC")
    )

    type = 'flutterwave'
    providers = [
        'flutterwave', 'pledge'
    ]

    provider_class = FlutterwavePaymentProvider

    account = models.CharField(
        _("flutterwave account"), max_length=100, null=True, blank=True)
    account_holder_name = models.CharField(
        _("account holder name"), max_length=100, null=True, blank=True)
    bank_country_code = models.CharField(
        _("bank country code"), max_length=2, default='NG', null=True, blank=True)
    bank_code = models.CharField(
        _("bank"), choices=BANK_CHOICES, max_length=100, null=True, blank=True)
    account_number = models.CharField(
        _("account number"), max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = _('Flutterwave bank account')
        verbose_name_plural = _('Flutterwave bank accounts')

    class JSONAPIMeta:
        resource_name = 'payout-accounts/flutterwave-external-accounts'
