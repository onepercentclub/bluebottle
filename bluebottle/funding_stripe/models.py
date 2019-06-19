from django.conf import settings
from django.db import models, connection
from django.utils.translation import ugettext_lazy as _

from bluebottle.funding_stripe import stripe
from bluebottle.fsm import TransitionManager
from bluebottle.funding.models import (
    Payment, PaymentProvider, KYCCheck
)
from bluebottle.funding_stripe.transitions import StripePaymentTransitions
from bluebottle.funding.transitions import KYCCheckTransitions
from bluebottle.payouts.models import StripePayoutAccount


class StripePayment(Payment):
    intent_id = models.CharField(max_length=30)
    client_secret = models.CharField(max_length=100)

    transitions = TransitionManager(StripePaymentTransitions, 'status')

    def save(self, *args, **kwargs):
        if not self.pk:
            intent = stripe.PaymentIntent.create(
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
        intent = stripe.PaymentIntent.retrieve(self.intent_id)

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


class StripeKYCCheck(KYCCheck):
    account_id = models.CharField(max_length=40)
    country = models.CharField(max_length=100)

    transitions = TransitionManager(KYCCheckTransitions, 'status')

    @property
    def account(self):
        if not self._account:
            self._account = stripe.Account.retrieve(self.account_id)

        return self._account

    def save(self, *args, **kwargs):
        if not self.account_id:
            account = stripe.Account.create(
                country=self.country
            )
            self.account_id = account.id

        super(StripeKYCCheck, self).save(*args, **kwargs)

    def update(self, token):
        self._account = stripe.Account.modify(
            self.account_id,
            token=token
        )

    @property
    def verified(self):
        return not self.account.requirements.eventually_due

    @property
    def required(self):
        return self.account.requirements.eventually_due

    @property
    def disabled(self):
        return self.account.requirements.disabled

    @property
    def personal_data(self):
        return self.account.individual

    @property
    def external_accounts(self):
        return self.account.external_accounts.data

    @property
    def metadata(self):
        return {
            "tenant_name": connection.tenant.client_name,
            "tenant_domain": connection.tenant.domain_url,
            "member_id": self.user.pk,
        }
