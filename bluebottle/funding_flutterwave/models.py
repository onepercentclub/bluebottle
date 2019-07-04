from django.db import models

from bluebottle.fsm import TransitionManager
from bluebottle.funding.models import Payment, PaymentProvider
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
        return [{
            'provider': 'flutterwave',
            'name': 'creditcard',
            'currencies': ['NGN'],
            'countries': ['NG']
        }]

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
