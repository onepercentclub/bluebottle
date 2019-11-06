from django.db import models
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm import TransitionManager
from bluebottle.funding.models import Payment, PaymentProvider, PaymentMethod, BankAccount
from bluebottle.funding.transitions import PaymentTransitions


class VitepayPaymentProvider(PaymentProvider):

    api_secret = models.CharField(max_length=100)
    prefix = models.CharField(max_length=10, default='goodup')
    api_key = models.CharField(max_length=100)
    api_url = models.CharField(max_length=100, default='https://api.vitepay.com/v1/prod/payments')

    provider = 'vitepay'

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

    class Meta:
        verbose_name = 'Vitepay payment provider'


class VitepayPayment(Payment):
    mobile_number = models.CharField(max_length=30, blank=True, null=True)
    unique_id = models.CharField(max_length=30)
    transitions = TransitionManager(PaymentTransitions, 'status')
    payment_url = models.CharField(max_length=200, blank=True, null=True)

    provider = 'vitepay'

    def update(self):
        pass

    def save(self, *args, **kwargs):
        if not self.unique_id:
            provider = VitepayPaymentProvider.objects.get()
            self.unique_id = format_html("{}-{}", provider.prefix, self.donation.id)
        super(VitepayPayment, self).save(*args, **kwargs)


class VitepayBankAccount(BankAccount):
    account_name = models.CharField(max_length=200, null=True, blank=True)
    mobile_number = models.CharField(max_length=40, null=True, blank=True)
    provider_class = VitepayPaymentProvider

    def save(self, *args, **kwargs):
        super(VitepayBankAccount, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _('Vitepay bank account')
        verbose_name_plural = _('Vitepay bank accounts')

    class JSONAPIMeta:
        resource_name = 'payout-accounts/vitepay-external-accounts'
