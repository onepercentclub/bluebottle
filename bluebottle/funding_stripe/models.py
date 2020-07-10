import re
import json
from operator import attrgetter

from django.utils.functional import cached_property
from djmoney.money import Money

from django_extensions.db.fields.json import JSONField

from bluebottle.funding.exception import PaymentException
from django.conf import settings
from django.db import ProgrammingError
from django.db import models, connection
from django.utils.translation import ugettext_lazy as _
from memoize import memoize
from stripe.error import AuthenticationError, StripeError

from bluebottle.fsm import TransitionManager
from bluebottle.funding.models import Donation
from bluebottle.funding.models import (
    Payment, PaymentProvider, PaymentMethod,
    PayoutAccount, BankAccount)
from bluebottle.funding.transitions import PayoutAccountTransitions
from bluebottle.funding_stripe.transitions import (
    StripePaymentTransitions,
    StripeSourcePaymentTransitions,
    StripePayoutAccountTransitions
)
from bluebottle.funding_stripe.utils import stripe
from bluebottle.utils.models import ValidatorError


class PaymentIntent(models.Model):
    intent_id = models.CharField(max_length=30)
    client_secret = models.CharField(max_length=100)
    donation = models.ForeignKey(Donation)

    def save(self, *args, **kwargs):
        if not self.pk:
            # FIXME: First verify that the funding activity has a valid Stripe account connected.

            statement_descriptor = connection.tenant.name[:22]

            account_id = self.donation.activity.bank_account.connect_account.account_id
            intent = stripe.PaymentIntent.create(
                amount=int(self.donation.amount.amount * 100),
                currency=self.donation.amount.currency,
                transfer_data={
                    'destination': account_id,
                },
                statement_descriptor=statement_descriptor,
                statement_descriptor_suffix=statement_descriptor[:18],
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

    def __unicode__(self):
        return self.intent_id


class StripePayment(Payment):
    payment_intent = models.OneToOneField(PaymentIntent, related_name='payment')
    transitions = TransitionManager(StripePaymentTransitions, 'status')

    provider = 'stripe'

    def refund(self):
        intent = self.payment_intent.intent
        charge = intent.charges.data[0]
        charge.refund(
            reverse_transfer=True,
        )
        self.save()

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
        elif intent.status == 'succeeded':
            transfer = stripe.Transfer.retrieve(intent.charges.data[0].transfer)
            self.donation.payout_amount = Money(
                transfer.amount / 100.0, transfer.currency
            )
            self.donation.save()
            if self.status != StripePaymentTransitions.values.succeeded:
                self.transitions.succeed()
                self.save()


class StripeSourcePayment(Payment):
    source_token = models.CharField(max_length=30)
    charge_token = models.CharField(max_length=30, blank=True, null=True)

    transitions = TransitionManager(StripeSourcePaymentTransitions, 'status')

    provider = 'stripe'

    @property
    def charge(self):
        if self.charge_token:
            return stripe.Charge.retrieve(self.charge_token)

    @property
    def source(self):
        if self.source_token:
            return stripe.Source.retrieve(self.source_token)

    def refund(self):
        charge = stripe.Charge.retrieve(self.charge_token)
        charge.refund(
            reverse_transfer=True,
        )

    def do_charge(self):
        account_id = self.donation.activity.bank_account.connect_account.account_id

        statement_descriptor = connection.tenant.name[:22]
        charge = stripe.Charge.create(
            amount=int(self.donation.amount.amount * 100),
            currency=self.donation.amount.currency,
            source=self.source_token,
            transfer_data={
                'destination': account_id,
            },
            statement_descriptor_suffix=statement_descriptor[:18],
            metadata=self.metadata
        )

        self.charge_token = charge.id
        self.transitions.charge()
        self.save()

    def update(self):
        try:
            # Update donation amount if it differs
            if self.source.amount / 100 != self.donation.amount.amount \
                    or self.source.currency != self.donation.amount.currency:
                self.donation.amount = Money(self.source.amount / 100, self.source.currency)
                self.donation.save()
            if not self.charge_token and self.source.status == 'chargeable':
                self.do_charge()
            if (not self.status == 'failed') and self.source.status == 'failed':
                self.transitions.fail()

            if (not self.status == 'canceled') and self.source.status == 'canceled':
                self.transitions.cancel()

            if self.charge_token:
                if (not self.status == 'failed') and self.charge.status == 'failed':
                    self.transitions.fail()

                if (not self.status == 'succeeded') and self.charge.status == 'succeeded':
                    self.transitions.succeed()

                if (not self.status == 'refunded') and self.charge.refunded:
                    self.transitions.refund()

                if (not self.status == 'disputed') and self.charge.dispute:
                    self.transitions.dispute()

            self.save()
        except StripeError as error:
            raise PaymentException(error.message)

    def save(self, *args, **kwargs):
        created = not self.pk

        super(StripeSourcePayment, self).save()

        if created:
            stripe.Source.modify(self.source_token, metadata=self.metadata)

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
            currencies=['EUR', 'USD', 'GBP', 'AUD'],
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

    class Meta:
        verbose_name = 'Stripe payment provider'


with open('bluebottle/funding_stripe/data/document_spec.json') as file:
    DOCUMENT_SPEC = json.load(file)


@memoize(timeout=60 * 60 * 24)
def get_specs(country):
    return stripe.CountrySpec.retrieve(country)


class StripePayoutAccount(PayoutAccount):
    account_id = models.CharField(max_length=40, help_text=_("Starts with 'acct_...'"))
    country = models.CharField(max_length=2)
    document_type = models.CharField(max_length=20, blank=True)
    eventually_due = JSONField(null=True, default=[])

    transitions = TransitionManager(StripePayoutAccountTransitions, 'status')

    @property
    def country_spec(self):
        return get_specs(self.country).verification_fields.individual

    @property
    def document_spec(self):
        for spec in DOCUMENT_SPEC:
            if spec['id'] == self.country:
                return spec
        for spec in DOCUMENT_SPEC:
            if spec['id'] == 'DEFAULT':
                return spec

    @property
    def errors(self):
        for error in super(StripePayoutAccount, self).errors:
            yield error

        if self.account_id and hasattr(self.account.requirements, 'errors'):
            for error in self.account.requirements.errors:
                if error['requirement'] == 'individual.verification.document':
                    requirement = 'individual.verification.document.front'
                else:
                    requirement = error['requirement']

                yield ValidatorError(
                    requirement, error['code'], error['reason']
                )

    @property
    def required_fields(self):
        fields = ['country', ]

        if self.account_id:
            fields += [
                field for field in self.eventually_due if
                field not in [
                    'external_account', 'tos_acceptance.date',
                    'tos_acceptance.ip', 'business_profile.url', 'business_profile.mcc',
                ]
            ]
            if 'individual.verification.additional_document' not in fields:
                fields.append('individual.verification.additional_document')

            if 'individual.verification.document' in fields:
                fields.remove('individual.verification.document')

            if 'document_type' not in fields:
                fields.append('document_type')

            if 'individual.verification.document.front' not in fields:
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
                elif field == 'individual.verification.additional_document':
                    try:
                        if attrgetter(
                            'individual.verification.additional_document.front'
                        )(self.account) in (None, ''):
                            yield field
                    except AttributeError:
                        yield field

                else:
                    try:
                        if attrgetter(field)(self.account) in (None, ''):
                            yield field
                    except AttributeError:
                        yield field
            else:
                try:
                    value = attrgetter(field)(self)
                    if value in (None, ''):
                        yield field
                except AttributeError:
                    yield field

        if not self.account.external_accounts.total_count > 0:
            yield 'external_account'

    @property
    def missing_fields(self):
        account_details = getattr(self.account, 'individual', None)
        if account_details:
            requirements = account_details.requirements
            missing = requirements.currently_due + requirements.eventually_due + requirements.past_due
            if getattr(self.account.requirements, 'disabled_reason', None):
                missing += [self.account.requirements.disabled_reason]
            if getattr(account_details.verification, 'document', None) and \
                    account_details.verification.document.details:
                missing += [account_details.verification.document.details]
            return missing
        return []

    @property
    def pending_fields(self):
        account_details = getattr(self.account, 'individual', None)
        if account_details:
            requirements = account_details.requirements
            return requirements.pending_verification
        return []

    def check_status(self):
        if self.account:
            del self.account
        account_details = getattr(self.account, 'individual', None)
        if account_details:
            if getattr(account_details.verification, 'document', None) and \
                    account_details.verification.document.details:
                if self.status != PayoutAccountTransitions.values.rejected:
                    self.transitions.reject()
            elif getattr(self.account.requirements, 'disabled_reason', None):
                if self.status != PayoutAccountTransitions.values.incomplete:
                    self.transitions.set_incomplete()
            elif len(self.missing_fields) == 0 and len(self.pending_fields) == 0:
                if self.status != PayoutAccountTransitions.values.verified:
                    self.transitions.verify()
            elif len(self.missing_fields):
                if self.status != PayoutAccountTransitions.values.incomplete:
                    self.transitions.set_incomplete()
            elif len(self.pending_fields):
                if self.status != PayoutAccountTransitions.values.pending:
                    # Submit to transition to pending
                    self.transitions.submit()
            else:
                if self.status != PayoutAccountTransitions.values.incomplete:
                    self.transitions.set_incomplete()
        else:
            if self.status != PayoutAccountTransitions.values.incomplete:
                self.transitions.set_incomplete()

        externals = self.account['external_accounts']['data']
        for external in externals:
            external_account, _created = ExternalAccount.objects.get_or_create(
                account_id=external['id']
            )
            external_account.account = external
            external_account.connect_account = self
            external_account.save()
        self.save()

    @cached_property
    def account(self):
        if not hasattr(self, '_account'):
            try:
                self._account = stripe.Account.retrieve(self.account_id)
            except AuthenticationError:
                self._account = {}
        return self._account

    def save(self, *args, **kwargs):

        if self.account_id and not self.country == self.account.country:
            self.account_id = None

        if not self.account_id:
            if len(self.owner.activities.all()):
                url = self.owner.activities.first().get_absolute_url()
            else:
                url = 'https://{}'.format(connection.tenant.domain_url)

            if 'localhost' in url:
                url = re.sub('localhost', 't.goodup.com', url)

            self._account = stripe.Account.create(
                country=self.country,
                type='custom',
                settings=self.account_settings,
                business_type='individual',
                requested_capabilities=["transfers"],
                business_profile={
                    'url': url,
                    'mcc': '8398'
                },
                metadata=self.metadata
            )
            self.account_id = self._account.id

        if self.account_id:
            for field in self.account.requirements.eventually_due:
                if field not in self.eventually_due:
                    self.eventually_due.append(field)

        super(StripePayoutAccount, self).save(*args, **kwargs)

    def update(self, token):
        self._account = stripe.Account.modify(
            self.account_id,
            account_token=token
        )

    @property
    def verified(self):
        return self.status == 'verified'

    @property
    def complete(self):
        return (
            'individual' in self.account and
            self.account.individual.verification.status == 'verified' and
            not self.account.individual.requirements.eventually_due
        )

    @property
    def rejected(self):
        return self.account.individual.verification.status == 'unverified'

    @property
    def disabled(self):
        return self.account.requirements.disabled

    @property
    def account_settings(self):
        statement_descriptor = connection.tenant.name[:22]
        while len(statement_descriptor) < 5:
            statement_descriptor += '-'
        return {
            'payouts': {
                'schedule': {
                    'interval': 'manual'
                },
                'statement_descriptor': statement_descriptor
            },
            'payments': {
                'statement_descriptor': statement_descriptor
            },
            'card_payments': {
                'statement_descriptor_prefix': statement_descriptor[:10]
            }
        }

    @property
    def metadata(self):
        return {
            "tenant_name": connection.tenant.client_name,
            "tenant_domain": connection.tenant.domain_url,
            "member_id": self.owner.pk,
        }

    class Meta:
        verbose_name = _('stripe payout account')
        verbose_name_plural = _('stripe payout accounts')

    class JSONAPIMeta:
        resource_name = 'payout-accounts/stripes'


class ExternalAccount(BankAccount):
    account_id = models.CharField(max_length=40, help_text=_("Starts with 'ba_...'"))
    provider_class = StripePaymentProvider

    @cached_property
    def account(self):
        if self.account_id:
            if not hasattr(self, '_account'):
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
    def verified(self):
        return self.connect_account.verified

    @property
    def metadata(self):
        return {
            "tenant_name": connection.tenant.client_name,
            "tenant_domain": connection.tenant.domain_url,
        }

    class JSONAPIMeta:
        resource_name = 'payout-accounts/stripe-external-accounts'

    class Meta:
        verbose_name = _('Stripe external account')
        verbose_name_plural = _('Stripe exterrnal account')

    def __unicode__(self):
        return "Stripe external account {}".format(self.account_id)
