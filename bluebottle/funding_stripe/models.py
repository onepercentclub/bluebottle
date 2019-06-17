from django.conf import settings
from django.db import models, connection
from django.utils.translation import ugettext_lazy as _

from bluebottle.funding.models import Payment, PaymentProvider
from bluebottle.funding_stripe.utils import StripeMixin
from bluebottle.payouts.models import StripePayoutAccount


class StripePayment(Payment, StripeMixin):
    intent_id = models.CharField(max_length=30)
    client_secret = models.CharField(max_length=100)

    def save(self, *args, **kwargs):
        if not self.pk:
            intent = self.stripe.PaymentIntent.create(
                amount=int(self.donation.amount.amount * 100),
                currency=self.donation.amount.currency,
                transfer_data={
                    'destination': StripePayoutAccount.objects.all()[0].account_id,
                },
                metadata=self.metadata
            )
            self.intent_id = intent.id
            self.client_secret = intent.client_secret

        super(StripePayment, self).save(*args, **kwargs)

    def update(self):
        intent = self.stripe.PaymentIntent.retrieve(self.intent_id)
        if len(intent.charges) == 0:
            # No charge. Do we still need to charge?
            self.fail()
            self.save()
        elif intent.charges.data[0].refunded and self.status != Payment.Status.refunded:
            self.refund()
            self.save()
        elif intent.status == 'failed' and self.status != Payment.Status.failed:
            self.fail()
            self.save()
        elif intent.status == 'succeeded' and self.status != Payment.Status.success:
            self.succeed()
            self.save()

    @property
    def metadata(self):
        return {
            "tenant_name": connection.tenant.client_name,
            "tenant_domain": connection.tenant.domain_url,
            "activity_id": self.donation.activity.pk,
            "activity_title": self.donation.activity.title,
        }

    @Payment.status.transition(
        source=['success'],
        target='refunded'
    )
    def request_refund(self):
        intent = self.stripe.PaymentIntent.retrieve(self.intent_id)

        intent.charges[0].refund(
            reverse_transfer=True,
        )


class StripePaymentProvider(PaymentProvider):

    stripe_payment_methods = {
        'credit_card': {
            'name': _('Credit card'),
            'currencies': ['EUR', 'USD'],
        },
        'bancontact': {
            'name': _('Bancontact'),
            'currencies': ['EUR'],
            'countries': ['BE']
        },
        'ideal': {
            'name': _('iDEAL'),
            'currencies': ['EUR'],
            'countries': ['NL']
        },
        'direct_debit': {
            'name': _('Direct debit'),
            'currencies': ['EUR'],
            'countries': ['NL', 'BE', 'DE']
        }
    }

    @property
    def public_settings(self):
        return settings.STRIPE['public']

    @property
    def private_settings(self):
        return settings.STRIPE['private']

    credit_card = models.BooleanField(_('Credit card'), default=True)
    ideal = models.BooleanField(_('iDEAL'), default=False)
    bancontact = models.BooleanField(_('Bancontact'), default=False)
    direct_debit = models.BooleanField(_('Direct debit'), default=False)

    @property
    def payment_methods(self):
        methods = []
        for method in ['credit_card', 'ideal', 'bancontact', 'direct_debit']:
            if getattr(self, method, False):
                method_settings = self.stripe_payment_methods[method]
                method_settings['code'] = method
                method_settings['provider'] = 'stripe'
                methods.append(method_settings)
        return methods
