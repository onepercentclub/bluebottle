from django.db import models
from django.utils.html import format_html

from bluebottle.fsm import TransitionManager
from bluebottle.funding.models import Payment, PaymentProvider, PaymentMethod, BankAccount
from bluebottle.funding.transitions import PaymentTransitions


class LipishaPaymentProvider(PaymentProvider):

    api_key = models.CharField(max_length=100)
    api_signature = models.CharField(max_length=500)
    prefix = models.CharField(max_length=100, default='goodup')
    paybill = models.CharField(max_length=10)

    @property
    def payment_methods(self):
        return [
            PaymentMethod(
                provider='lipisha',
                name='M-PESA',
                currencies=['KES'],
                code='mpesa'
            )
        ]

    @property
    def private_settings(self):
        return {
            'api_key': self.api_key,
            'api_signature': self.api_signature
        }

    class Meta:
        verbose_name = 'Lipisha payment provider'


class LipishaPayment(Payment):
    mobile_number = models.CharField(max_length=30, blank=True, null=True)
    method = models.CharField(max_length=30, default='Paybill (M-Pesa)')
    transaction = models.CharField(max_length=200, blank=True, null=True)
    unique_id = models.CharField(max_length=30)
    transitions = TransitionManager(PaymentTransitions, 'status')

    def update(self):
        pass

    def save(self, *args, **kwargs):
        if not self.unique_id:
            provider = LipishaPaymentProvider.objects.get()
            self.unique_id = format_html("{}-{}", provider.prefix, self.donation.id)
        super(LipishaPayment, self).save(*args, **kwargs)


class LipishaBankAccount(BankAccount):
    provider_class = LipishaPaymentProvider

    account_number = models.CharField(max_length=50, blank=True, null=True)
    account_name = models.CharField(max_length=200, blank=True, null=True)
    bank_code = models.CharField(max_length=50, blank=True, null=True)
    branch_name = models.CharField(max_length=200, blank=True, null=True)
    branch_code = models.CharField(max_length=200, blank=True, null=True)
    address = models.CharField(max_length=500, blank=True, null=True)
    swift = models.CharField('SWIFT/Routing Code', max_length=50, blank=True, null=True)

    def save(self, *args, **kwargs):
        super(LipishaBankAccount, self).save(*args, **kwargs)
