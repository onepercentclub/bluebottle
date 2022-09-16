from __future__ import absolute_import
from builtins import object
from django.db import models
from django.utils.translation import gettext_lazy as _

from bluebottle.funding.models import Payment, PaymentProvider, PaymentMethod, BankAccount
from bluebottle.funding_flutterwave.utils import check_payment_status


class FlutterwavePayment(Payment):
    tx_ref = models.CharField(max_length=30, unique=True)
    provider = 'flutterwave'

    def update(self):
        check_payment_status(self)

    def refund(self):
        raise NotImplementedError


class FlutterwavePaymentProvider(PaymentProvider):

    title = 'Flutterwave'

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
                currencies=['NGN', 'KES', 'USD'],
            ),
            PaymentMethod(
                provider='flutterwave',
                name='M-PESA/Airtel',
                code='mpesa',
                currencies=['KES'],
            ),
            # PaymentMethod(
            #     provider='flutterwave',
            #     name='PayPal',
            #     code='paypal',
            #     currencies=['NGN', 'USD'],
            # ),
            PaymentMethod(
                provider='flutterwave',
                name='OrangeMoney',
                code='orangemoney',
                currencies=['XOF'],
            ),
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

    class Meta(object):
        verbose_name = 'Flutterwave payment provider'


class FlutterwaveBankAccount(BankAccount):

    BANK_CHOICES = (
        ("", "Select bank"),
        # NGN
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
        ("057", "Zenith bank PLC"),
        # KE
        ("01", "Kenya Commercial Bank Limited"),
        ("11", "Co-operative Bank of Kenya Limited"),
        ("31", "CFC Stanbic Bank Kenya Limited"),
        ("41", "NIC Bank Limited"),
        ("51", "Jamii Bora Bank"),
        ("61", "Housing Finance Bank"),
        ("14", "Oriental Commercial Bank Limited"),
        ("54", "Victoria Commercial Bank Limited"),
        ("07", "Commercial Bank of Africa Limited"),
        ("49", "Equatorial Commercial Bank Limited"),
        ("57", "Investments n Mortgages Bank Limited"),
        ("39", "Imperial Bank Limited"),
        ("12", "National Bank of Kenya Limited"),
        ("72", "Gulf African Bank Ltd"),
        ("25", "Credit Bank Limited"),
        ("35", "African Banking Corp. Bank Ltd"),
        ("74", "First Community Bank"),
        ("55", "Guardian Bank Limited"),
        ("10", "Prime Bank Limited"),
        ("20", "Dubai Bank Kenya Limited"),
        ("30", "Chase Bank Limited"),
        ("50", "Paramount Universal Bank Limited"),
        ("70", "Family Bank Ltd"),
        ("23", "Consolidated Bank of Kenya Limited"),
        ("18", "Middle East Bank Kenya Limited"),
        ("63", "Diamond Trust Bank Limited"),
        ("16", "Citibank N.A."),
        ("26", "Trans-National Bank Limited"),
        ("68", "Equity Bank Limited"),
        ("66", "K-Rep Bank Limited"),
        ("76", "UBA Kenya Bank Ltd"),
        ("19", "Bank of  Africa Kenya Limited"),
        ("10276", "ABSA Bank Kenya PLC"),
        ("02", "Standard Chartered Bank Limited")

    )
    COUNTRY_CHOICES = (
        ("KE", "Kenya"),
        ("NG", "Nigeria"),
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

    class Meta(object):
        verbose_name = _('Flutterwave bank account')
        verbose_name_plural = _('Flutterwave bank accounts')

    class JSONAPIMeta(object):
        resource_name = 'payout-accounts/flutterwave-external-accounts'

    @property
    def bank_name(self):
        if not self.bank_code:
            return None
        return [bank[1] for bank in self.BANK_CHOICES if bank[0] == self.bank_code][0]

    def __str__(self):
        return "Flutterwave Bankaccount {}".format(self.account_holder_name)


from .states import *  # noqa
