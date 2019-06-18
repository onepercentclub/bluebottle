from django.db import models

from bluebottle.funding.models import Payment, PaymentProvider


class VitepayPayment(Payment):
    intent_id = models.CharField(max_length=30)
    client_secret = models.CharField(max_length=100)

    @property
    def unique_id(self):
        return "Payment-{}".format(self.id)


class VitepayPaymentProvider(PaymentProvider):

    api_secret = models.CharField(max_length=100)
    api_key = models.CharField(max_length=100)
    api_url = models.CharField(max_length=100, default='https://api.vitepay.com/v1/prod/payments')

    @property
    def payment_methods(self):
        return [{
            'provider': 'vitepay',
            'name': 'orange_money',
            'currencies': ['XOF'],
            'countries': ['ML']
        }]

    @property
    def private_settings(self):
        return {
            'api_secret': self.api_secret,
            'api_key': self.api_key,
            'api_url': self.api_url
        }
