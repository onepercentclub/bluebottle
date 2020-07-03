from django.db import models
from django.utils.translation import ugettext_lazy as _

from bluebottle.funding.models import Payment, PaymentProvider, PaymentMethod, BankAccount


class TelesomPaymentProvider(PaymentProvider):

    merchant_uid = models.CharField(max_length=100)
    api_user_id = models.CharField(max_length=100)
    api_key = models.CharField(max_length=100)
    api_url = models.CharField(max_length=100, default='https://sandbox.safarifoneict.com/asm/')
    prefix = models.CharField(max_length=10, default='goodup')

    @property
    def payment_methods(self):
        return [
            PaymentMethod(
                provider='telesom',
                name='Zaad',
                currencies=['USD'],
                code='zaad'
            )
        ]

    @property
    def private_settings(self):
        return {
            'merchant_uid': self.merchant_uid,
            'api_user_id': self.api_user_id,
            'api_key': self.api_key,
            'api_url': self.api_url
        }

    class Meta:
        verbose_name = 'Telesom payment provider'


class TelesomPayment(Payment):
    account_number = models.CharField(max_length=30, blank=True, null=True)
    account_name = models.CharField(max_length=30, blank=True, null=True)

    unique_id = models.CharField(max_length=30)

    reference_id = models.CharField(max_length=100)
    transaction_id = models.CharField(max_length=100)
    transaction_amount = models.CharField(max_length=100)
    issuer_transaction_id = models.CharField(max_length=100)

    provider = 'vitepay'

    """
    "issuerApprovalCode": "",
    "accountNo": "2526****0002",
    "accountType": "MWALLET_ACCOUNT",
    "accountholder": "henk",
    "state": "APPROVED",
    "merchantCharges": "2.5",
    "customerCharges": "0.0",
    "referenceId": "56werw278",
    "transactionId": "1236292",
    "accountExpDate": "",
    "issuerTransactionId": "ISR0011236292",
    "txAmount": "50.0"
    """

    def update(self):
        pass

    def save(self, *args, **kwargs):
        if not self.unique_id:
            provider = TelesomPaymentProvider.objects.get()
            self.unique_id = "{}-{}".format(provider.prefix, self.donation.id)
        super(TelesomPayment, self).save(*args, **kwargs)


class TelesomBankAccount(BankAccount):
    account_name = models.CharField(max_length=200, null=True, blank=True)
    mobile_number = models.CharField(max_length=40, null=True, blank=True)
    provider_class = TelesomPaymentProvider

    def save(self, *args, **kwargs):
        super(TelesomBankAccount, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _('Telesom bank account')
        verbose_name_plural = _('Telesom bank accounts')

    class JSONAPIMeta:
        resource_name = 'payout-accounts/telesom-external-accounts'


from states import *  # noqa
