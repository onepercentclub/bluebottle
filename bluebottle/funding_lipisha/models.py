from django.db import models
from django.utils.html import format_html

from bluebottle.fsm import TransitionManager
from bluebottle.funding.models import Payment, PaymentProvider, PaymentMethod
from bluebottle.funding.transitions import PaymentTransitions


class LipishaPaymentProvider(PaymentProvider):

    api_key = models.CharField(max_length=100)
    api_signature = models.CharField(max_length=500)

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
    unique_id = models.CharField(max_length=30)
    transitions = TransitionManager(PaymentTransitions, 'status')
    payment_url = models.CharField(max_length=200, blank=True, null=True)

    def update(self):
        pass

    def save(self, *args, **kwargs):
        if not self.unique_id:
            provider = LipishaPaymentProvider.objects.get()
            self.unique_id = format_html("{}-{}", provider.prefix, self.donation.id)
        super(LipishaPayment, self).save(*args, **kwargs)
