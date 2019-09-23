import json
from memoize import memoize
from operator import attrgetter

from django.conf import settings
from django.db import ProgrammingError
from django.db import models, connection
from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm import TransitionManager
from bluebottle.funding.models import Donation
from bluebottle.funding.models import (
    Payment, PaymentProvider, PaymentMethod,
    PayoutAccount, BankAccount)
from bluebottle.funding_stripe.transitions import StripePaymentTransitions
from bluebottle.funding_stripe.transitions import StripeSourcePaymentTransitions
from bluebottle.funding_stripe.utils import stripe


class PaymentIntent(models.Model):
    intent_id = models.CharField(max_length=30)
    client_secret = models.CharField(max_length=100)
    donation = models.ForeignKey(Donation)

    def save(self, *args, **kwargs):
        if not self.pk:
            # FIXME: First verify that the funding activity has a valid Stripe account connected.
            account_id = self.donation.activity.account.account_id
            intent = stripe.PaymentIntent.create(
                amount=int(self.donation.amount.amount * 100),
                currency=self.donation.amount.currency,
                transfer_data={
                    'destination': account_id,
                },
                metadata=self.metadata
            )
            self.intent_id = intent.id
            self.client_secret = intent.client_secret

        super(PaymentIntent, self).save(*args, **kwargs)

    @property
    def intent(self):
        return stripe.PaymentIntent.retrieve(self.intent_id)

    @property
    def metadata(self):
        return {
            "tenant_name": connection.tenant.client_name,
            "tenant_domain": connection.tenant.domain_url,
            "activity_id": self.donation.activity.pk,
            "activity_title": self.donation.activity.title,
        }

    class JSONAPIMeta:
        resource_name = 'payments/stripe-payment-intents'


class StripePayment(Payment):
    payment_intent = models.OneToOneField(PaymentIntent, related_name='payment')
    transitions = TransitionManager(StripePaymentTransitions, 'status')

    def update(self):
        intent = self.payment_intent.intent
        if len(intent.charges) == 0:
            # No charge. Do we still need to charge?
            self.transitions.fail()
            self.save()
        elif intent.charges.data[0].refunded and self.status != StripePaymentTransitions.values.refunded:
            self.transitions.refund()
            self.save()
        elif intent.status == 'failed' and self.status != StripePaymentTransitions.values.failed:
            self.transitions.fail()
            self.save()
        elif intent.status == 'succeeded' and self.status != StripePaymentTransitions.values.succeeded:
            self.transitions.succeed()
            self.save()


class StripeSourcePayment(Payment):
    source_token = models.CharField(max_length=30)
    charge_token = models.CharField(max_length=30, blank=True, null=True)

    transitions = TransitionManager(StripeSourcePaymentTransitions, 'status')

    def charge(self):
        charge = stripe.Charge.create(
            amount=self.donation.amount,
            currency=self.donation.amount.currency,
            source=self.source_token,
            destination={
                'destination': StripePayoutAccount.objects.all()[0].account_id,
            },
            metadata=self.metadata
        )

        self.charge_token = charge.id
        self.transitions.charge()
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
            code='credit-card',
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
            code='direct-debit',
            name=_('Direct debit'),
            currencies=['EUR'],
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
            'credit-card': self.credit_card,
            'ideal': self.ideal,
            'bancontact': self.bancontact,
            'direct-debit': self.direct_debit
        }

    @property
    def private_settings(self):
        return {
            'api_key': settings.STRIPE['api_key'],
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
        for code in ['credit-card', 'ideal', 'bancontact', 'direct-debit']:
            if getattr(self, code.replace('-', '_'), False):
                for method in self.stripe_payment_methods:
                    if method.code == code:
                        methods.append(method)
        return methods


with open('bluebottle/funding_stripe/data/document_spec.json') as file:
    DOCUMENT_SPEC = json.load(file)


@memoize(timeout=60 * 60 * 24)
def get_specs(country):
    print '1111'
    return stripe.CountrySpec.retrieve(country)


class StripePayoutAccount(PayoutAccount):
    account_id = models.CharField(max_length=40)
    country = models.CharField(max_length=2)
    document_type = models.CharField(max_length=20, blank=True)

    provider_class = StripePaymentProvider

    @property
    def country_spec(self):
        return get_specs(self.country).verification_fields.individual

    @property
    def document_spec(self):
        for spec in DOCUMENT_SPEC:
            if spec['id'] == self.country:
                return spec

    @property
    def required_fields(self):
        fields = ['country', ]

        if self.account_id:
            fields += [
                field for field in self.country_spec['additional'] + self.country_spec['minimum'] if
                field not in ['business_type', 'external_account', 'tos_acceptance.date', 'tos_acceptance.ip', ]
            ]

            if 'individual.verification.document' in fields:
                fields.remove('individual.verification.document')

                fields.append('document_type')
                fields.append('individual.verification.document.front')

                if self.document_type in self.document_spec['document_types_requiring_back']:
                    fields.append('individual.verification.document.back')

            dob_fields = [field for field in fields if '.dob' in field]
            if dob_fields:
                fields.append('individual.dob')
                for field in dob_fields:
                    fields.remove(field)

        return fields

    @property
    def required(self):
        for field in self.required_fields:
            if field.startswith('individual'):
                if field == 'individual.dob':
                    try:
                        if not self.account.individual.dob.year:
                            yield 'individual.dob'
                    except AttributeError:
                        yield 'individual.dob'
                else:
                    try:
                        if attrgetter(field)(self.account) in (None, ''):
                            yield field
                    except AttributeError:
                        yield field
            else:
                value = attrgetter(field)(self)
                if value in (None, ''):
                    yield field

        if not self.account.external_accounts.total_count > 0:
            yield 'external_account'

    @property
    def account(self):
        if not hasattr(self, '_account'):
            self._account = stripe.Account.retrieve(self.account_id)

        return self._account

    def save(self, *args, **kwargs):
        if self.account_id and not self.country == self.account.country:
            self.account_id = None

        if not self.account_id:
            self._account = stripe.Account.create(
                country=self.country,
                type='custom',
                settings=self.account_settings,
                business_type='individual',
                metadata=self.metadata
            )
            self.account_id = self._account.id

        super(StripePayoutAccount, self).save(*args, **kwargs)

    def update(self, token):
        self._account = stripe.Account.modify(
            self.account_id,
            account_token=token
        )

    @property
    def verified(self):
        return (
            'individual' in self.account and
            self.account.individual.verification.status == 'verified' and
            not self.account.individual.requirements.eventually_due
        )

    @property
    def disabled(self):
        return self.account.requirements.disabled

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


class ExternalAccount(BankAccount):
    connect_account = models.ForeignKey(StripePayoutAccount, related_name='external_accounts')
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

    class JSONAPIMeta:
        resource_name = 'payout-accounts/stripe-external-accounts'
