from django.db import models
from django.utils.html import format_html

from bluebottle.fsm import TransitionManager
from bluebottle.funding.models import Payment, PaymentProvider, PaymentMethod, PayoutAccount
from bluebottle.funding.transitions import PaymentTransitions


class LipishaPaymentProvider(PaymentProvider):

    api_key = models.CharField(max_length=100)
    api_signature = models.CharField(max_length=500)
    prefix = models.CharField(max_length=100, default='goodup')
    paybill = models.CharField(max_length=10)

    currencies = ['KES']
    countries = ['KE']

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


class LipishaPayoutAccount(PayoutAccount):
    account_number = models.CharField(max_length=40)
    provider_class = LipishaPaymentProvider

    def save(self, *args, **kwargs):
        super(LipishaPayoutAccount, self).save(*args, **kwargs)
