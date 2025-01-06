from __future__ import absolute_import
from builtins import object
from django.db import models
from django.utils.translation import gettext_lazy as _

from bluebottle.funding.models import Payment, PaymentProvider, PaymentMethod, BankAccount


class VitepayPaymentProvider(PaymentProvider):

    title = 'Vitepay / Orange Money'
    provider = 'vitepay'

    api_secret = models.CharField(max_length=100)
    prefix = models.CharField(max_length=10, default='goodup')
    api_key = models.CharField(max_length=100)
    api_url = models.CharField(max_length=100, default='https://api.vitepay.com/v1/prod/payments')

    @property
    def payment_methods(self):
        return [
            PaymentMethod(
                provider='vitepay',
                name='Orange Money',
                currencies=['XOF'],
                code='orange_money'
            )
        ]

    @property
    def private_settings(self):
        return {
            'api_secret': self.api_secret,
            'api_key': self.api_key,
            'api_url': self.api_url
        }

    class Meta(object):
        verbose_name = 'Vitepay payment provider'


class VitepayPayment(Payment):
    mobile_number = models.CharField(max_length=30, blank=True, null=True)
    unique_id = models.CharField(max_length=30)
    payment_url = models.CharField(max_length=200, blank=True, null=True)

    provider = 'vitepay'

    def update(self):
        pass

    def save(self, *args, **kwargs):
        if not self.unique_id:
            provider = VitepayPaymentProvider.objects.get()
            self.unique_id = "{}-{}".format(provider.prefix, self.donation.id)
        super(VitepayPayment, self).save(*args, **kwargs)


class VitepayBankAccount(BankAccount):
    account_name = models.CharField(max_length=200, null=True, blank=True)
    mobile_number = models.CharField(max_length=40, null=True, blank=True)
    provider_class = VitepayPaymentProvider
    provider = 'vitepay'

    def save(self, *args, **kwargs):
        super(VitepayBankAccount, self).save(*args, **kwargs)

    class Meta(object):
        verbose_name = _('Vitepay bank account')
        verbose_name_plural = _('Vitepay bank accounts')

    class JSONAPIMeta(object):
        resource_name = 'payout-accounts/vitepay-external-accounts'

    def __str__(self):
        return u"Vitepay Bankaccount {}".format(self.account_name)

from .states import *  # noqa
