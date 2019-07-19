from django.conf import settings
from django.db import models, connection
from django.db import ProgrammingError
from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm import TransitionManager
from bluebottle.funding.models import (
    Payment, PaymentProvider, PaymentMethod, PayoutAccount
)
from bluebottle.funding_stripe.transitions import StripePaymentTransitions
from bluebottle.funding_stripe.utils import stripe
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

    stripe_payment_methods = [
        PaymentMethod(
            provider='stripe',
            code='credit_card',
            name=_('Credit card'),
            currencies=['EUR', 'USD'],
            countries=[]
        ),
        PaymentMethod(
            provider='stripe',
            code='bancontact',
            name=_('Bancontact'),
            currencies=['EUR'],
            countries=['BE']
        ),
        PaymentMethod(
            provider='stripe',
            code='ideal',
            name=_('iDEAL'),
            currencies=['EUR'],
            countries=['NL']
        ),
        PaymentMethod(
            provider='stripe',
            code='direct_debit',
            name=_('Direct debit'),
            currencies=['EUR'],
            countries=[]
        )
    ]

    currencies = ['EUR', 'USD']
    countries = ['AU', 'AT', 'BE', 'BR', 'CA', 'DK', 'FI', 'FR',
                 'DE', 'IE', 'LU', 'MX', 'NL', 'NZ', 'NO', 'PT',
                 'ES', 'SE', 'CH', 'GB', 'US']

    @property
    def public_settings(self):
        return {
            'publishable_key': settings.STRIPE['publishable_key'],
            'credit_card': self.credit_card,
            'ideal': self.ideal,
            'bancontact': self.bancontact,
            'direct_debit': self.direct_debit
        }

    @property
    def private_settings(self):
        return {
            'secret_key': settings.STRIPE['secret_key'],
            'webhook_secret': settings.STRIPE['webhook_secret'],
            'webhook_secret_connect': settings.STRIPE['webhook_secret_connect'],
        }

    credit_card = models.BooleanField(_('Credit card'), default=True)
    ideal = models.BooleanField(_('iDEAL'), default=False)
    bancontact = models.BooleanField(_('Bancontact'), default=False)
    direct_debit = models.BooleanField(_('Direct debit'), default=False)

    @property
    def payment_methods(self):
        methods = []
        for code in ['credit_card', 'ideal', 'bancontact', 'direct_debit']:
            if getattr(self, code, False):
                for method in self.stripe_payment_methods:
                    if method.code == code:
                        methods.append(method)
        return methods


class ConnectAccount(PayoutAccount):
    account_id = models.CharField(max_length=40)
    country = models.CharField(max_length=2)

    @property
    def account(self):
        if not hasattr(self, '_account'):
            self._account = stripe.Account.retrieve(self.account_id)

        return self._account

    def save(self, *args, **kwargs):
        if not self.account_id:
            self._account = stripe.Account.create(
                country=self.country,
                type='custom',
                settings=self.account_settings,
                business_type='individual',
                metadata=self.metadata
            )
            self.account_id = self._account.id
            self.transitions.submit()

        super(ConnectAccount, self).save(*args, **kwargs)

    def update(self, token):
        self._account = stripe.Account.modify(
            self.account_id,
            account_token=token
        )

    @property
    def verified(self):
        return (
            not self.account.requirements.eventually_due and
            self.account.individual.verification.status == 'verified'
        )

    @property
    def required(self):
        return self.account.requirements.eventually_due

    @property
    def disabled(self):
        return self.account.requirements.disabled

    @property
    def individual(self):
        return self.account.individual

    @property
    def tos_acceptance(self):
        return self.account.tos_acceptance

    @property
    def account_settings(self):
        statement_descriptor = connection.tenant.name[:21]
        return {
            'payouts': {
                'schedule': {
                    'interval': 'manual'
                }
            },
            'payments': {
                'statement_descriptor': statement_descriptor
            }
        }

    @property
    def metadata(self):
        return {
            "tenant_name": connection.tenant.client_name,
            "tenant_domain": connection.tenant.domain_url,
            "member_id": self.owner.pk,
        }


class ExternalAccount(models.Model):
    connect_account = models.ForeignKey(ConnectAccount, related_name='external_accounts')
    account_id = models.CharField(max_length=40)

    @property
    def account(self):
        if self.account_id:
            for account in self.connect_account.account.external_accounts:
                if account.id == self.account_id:
                    self._account = account

            if not hasattr(self, '_account'):
                self._account = self.connect_account.account.external_accounts.retrieve(self.account_id)

            return self._account

    def create(self, token):
        if self.account_id:
            raise ProgrammingError('Stripe Account is already created')

        self._account = stripe.Account.create_external_account(
            self.connect_account.account_id,
            external_account=token
        )
        self.account_id = self._account.id
        self.save()

    @property
    def metadata(self):
        return {
            "tenant_name": connection.tenant.client_name,
            "tenant_domain": connection.tenant.domain_url,
        }
