import json
from builtins import object

from django.conf import settings
from django.db import models, connection
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_better_admin_arrayfield.models.fields import ArrayField
from djchoices import DjangoChoices, ChoiceItem
from djmoney.money import Money
from future.utils import python_2_unicode_compatible
from memoize import memoize
from past.utils import old_div
from stripe.error import AuthenticationError, StripeError

from bluebottle.funding.exception import PaymentException
from bluebottle.funding.models import Donor, Funding
from bluebottle.funding.models import (
    Payment, PaymentProvider, PayoutAccount, BankAccount)
from bluebottle.funding_stripe.utils import get_stripe
from bluebottle.utils.utils import get_current_host


@python_2_unicode_compatible
class PaymentIntent(models.Model):
    intent_id = models.CharField(max_length=30)
    client_secret = models.CharField(max_length=100)
    donation = models.ForeignKey(Donor, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    instructions = models.JSONField(blank=True, null=True)

    @property
    def intent(self):
        stripe = get_stripe()
        return stripe.PaymentIntent.retrieve(self.intent_id)

    @property
    def metadata(self):
        return {
            "tenant_name": connection.tenant.client_name,
            "tenant_domain": connection.tenant.domain_url,
            "activity_id": self.donation.activity.pk,
            "activity_title": self.donation.activity.title,
        }

    class JSONAPIMeta(object):
        resource_name = 'payments/stripe-payment-intents'

    def get_payment(self):
        try:
            return self.payment
        except StripePayment.DoesNotExist:
            try:
                self.donation.payment.payment_intent = self
                self.donation.payment.save()
                return self.payment
            except Donor.payment.RelatedObjectDoesNotExist:
                return StripePayment.objects.create(payment_intent=self, donation=self.donation)

    def __str__(self):
        return self.intent_id


class StripePayment(Payment):
    payment_intent = models.OneToOneField(PaymentIntent, related_name='payment', on_delete=models.CASCADE)

    provider = 'stripe'

    def refund(self):
        stripe = get_stripe()

        intent = self.payment_intent.intent
        charge = intent.charges.data[0]

        stripe.Refund.create(charge=charge, reverse_transfer=True)

    def update(self):
        stripe = get_stripe()
        intent = self.payment_intent.intent
        if intent.status == 'requires_action' and self.status != self.states.action_needed.value:
            self.states.require_action(save=True)
        elif len(intent.charges) == 0 and self.status != self.states.action_needed.value:
            # No charge. Do we still need to charge?
            self.states.fail(save=True)
        elif len(intent.charges) > 0 and intent.charges.data[0].refunded and self.status != self.states.refunded.value:
            self.states.refund(save=True)
        elif intent.status == 'pending' and self.status != self.states.pending.value:
            self.states.authorize(save=True)
        elif intent.status == 'failed' and self.status != self.states.failed.value:
            self.states.fail(save=True)
        elif intent.status == 'succeeded':
            transfer = stripe.Transfer.retrieve(intent.charges.data[0].transfer)
            self.donation.payout_amount = Money(
                transfer.amount / 100.0, transfer.currency
            )

            if (
                    self.donation.amount.currency == transfer.currency
                    and self.donation.amount.amount != transfer.amount / 100.00
            ):
                self.donation.amount = Money(
                    transfer.amount / 100.0, transfer.currency
                )

            self.donation.save()
            if self.status != self.states.succeeded.value:
                self.states.succeed(save=True)

        return intent


class StripeSourcePayment(Payment):
    source_token = models.CharField(max_length=30)
    charge_token = models.CharField(max_length=30, blank=True, null=True)

    provider = 'stripe'

    @property
    def charge(self):
        if self.charge_token:
            stripe = get_stripe()
            return stripe.Charge.retrieve(self.charge_token)

    @property
    def source(self):
        if self.source_token:
            stripe = get_stripe()
            return stripe.Source.retrieve(self.source_token)

    def refund(self):
        stripe = get_stripe()
        stripe.Refund.create(charge=self.charge_token, reverse_transfer=True)

    def do_charge(self):
        stripe = get_stripe()
        connect_account = self.donation.activity.bank_account.connect_account

        statement_descriptor = connection.tenant.name[:22]
        charge_args = dict(
            amount=int(self.donation.amount.amount * 100),
            source=self.source_token,
            currency=self.donation.amount.currency,
            transfer_data={
                'destination': connect_account.account_id,
            },
            statement_descriptor_suffix=statement_descriptor[:18],
            metadata=self.metadata
        )

        charge = stripe.Charge.create(**charge_args)

        self.charge_token = charge.id
        self.states.charge(save=True)

    def update(self):
        try:
            # Update donation amount if it differs
            if old_div(self.source.amount, 100) != self.donation.amount.amount \
                    or self.source.currency != self.donation.amount.currency:
                self.donation.amount = Money(old_div(self.source.amount, 100), self.source.currency)
                self.donation.save()
            if not self.charge_token and self.source.status == 'chargeable':
                self.do_charge()
            if (not self.status == 'failed') and self.source.status == 'failed':
                self.states.fail(save=True)

            if (not self.status == 'canceled') and self.source.status == 'canceled':
                self.states.cancel(save=True)

            if self.charge_token:
                if self.charge.status == 'failed':
                    if self.status != 'failed':
                        self.states.fail(save=True)
                elif self.charge.refunded:
                    if self.status != 'refunded':
                        self.states.refund(save=True)
                elif self.charge.dispute:
                    if self.status != 'disputed':
                        self.states.dispute(save=True)
                elif self.charge.status == 'succeeded':
                    if self.status != 'succeeded':
                        self.states.succeed(save=True)

        except StripeError as error:
            raise PaymentException(error)

    def save(self, *args, **kwargs):
        created = not self.pk

        super(StripeSourcePayment, self).save()

        if created:
            stripe = get_stripe()
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
    title = 'Stripe'

    stripe_publishable_key = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name=_('Stripe publishable key'),
        help_text=_('This is only needed if you want to use a specific Stripe account.')
    )

    stripe_secret = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name=_('Stripe secret key'),
        help_text=_('This is only needed if you want to use a specific Stripe account.')
    )

    webhook_secret_connect = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name=_('Stripe connect webhook secret'),
        help_text=_('The secret for connect webhook.')
    )

    webhook_secret_intents = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name=_('Stripe payment intents webhook secret'),
        help_text=_('The secret for payment intents webhook.')
    )

    webhook_secret_sources = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name=_('Stripe payment sources webhook secret'),
        help_text=_('The secret for payment sources webhook.')
    )

    currency = models.CharField(
        max_length=3,
        default='EUR',
        verbose_name=_('Currency'),
        help_text=_('The currency for the global account.')
    )

    refund_enabled = True

    @property
    def public_settings(self):
        return {
            'publishable_key': self.stripe_publishable_key or settings.STRIPE['publishable_key'],
        }

    @property
    def private_settings(self):
        return {
            'api_key': self.stripe_secret or settings.STRIPE['api_key'],
            'webhook_secret': self.stripe_secret or settings.STRIPE['webhook_secret'],
            'webhook_secret_connect': self.stripe_secret or settings.STRIPE['webhook_secret_connect'],
        }

    class Meta(object):
        verbose_name = 'Stripe payment provider'


with open('bluebottle/funding_stripe/data/document_spec.json') as file:
    DOCUMENT_SPEC = json.load(file)


@memoize(timeout=60 * 60 * 24)
def get_specs(country):
    stripe = get_stripe()
    return stripe.CountrySpec.retrieve(country=country)


STRIPE_EUROPEAN_COUNTRY_CODES = [
    "AD", "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE",
    "FO", "FI", "FR", "DE", "GI", "GR", "GL", "GG", "VA",
    "HU", "IS", "IE", "IM", "IL", "IT", "JE", "LV", "LI",
    "LT", "LU", "MT", "MC", "NL", "NO", "PL", "PT", "RO",
    "PM", "SM", "SK", "SI", "ES", "SE", "TR", "GB"
]


class BusinessTypeChoices(DjangoChoices):
    company = ChoiceItem(
        'company',
        label=_("Commercial company")
    )
    individual = ChoiceItem(
        'individual',
        label=_("Individual person")
    )
    non_profit = ChoiceItem(
        'non_profit',
        label=_("Non-profit organization")
    )


class StripePayoutAccount(PayoutAccount):
    account_id = models.CharField(max_length=40, null=True, blank=True, help_text=_("Starts with 'acct_...'"))
    country = models.CharField(max_length=2)
    business_type = models.CharField(
        max_length=100,
        blank=True,
        choices=BusinessTypeChoices.choices,
        default=BusinessTypeChoices.individual

    )

    verified = models.BooleanField(default=False)

    payments_enabled = models.BooleanField(default=False)
    payouts_enabled = models.BooleanField(default=False)

    requirements = ArrayField(models.CharField(max_length=60), default=list)
    tos_accepted = models.BooleanField(default=False)

    provider = 'stripe'

    @property
    def account_settings(self):
        statement_descriptor = connection.tenant.name[:22]
        while len(statement_descriptor) < 5:
            statement_descriptor += "-"
        return {
            "payouts": {
                "schedule": {"interval": "manual"},
                "statement_descriptor": statement_descriptor,
            },
            "payments": {"statement_descriptor": statement_descriptor},
            "card_payments": {"statement_descriptor_prefix": statement_descriptor[:10]},
        }

    @property
    def metadata(self):
        return {
            "tenant_name": connection.tenant.client_name,
            "tenant_domain": connection.tenant.domain_url,
            "member_id": self.owner.pk,
        }

    def save(self, *args, **kwargs):
        stripe = get_stripe()

        if self.country and not self.account_id:
            if Funding.objects.filter(owner=self.owner).count():
                url = (
                    Funding.objects.filter(owner=self.owner).first().get_absolute_url()
                )
            else:
                url = "https://{}".format(connection.tenant.domain_url)

            if "localhost" in url:
                url = "https://goodup.com"

            account = stripe.Account.create(
                country=self.country,
                type="custom",
                settings=self.account_settings,
                business_type=self.business_type,
                capabilities={
                    "transfers": {"requested": True},
                    "card_payments": {"requested": True},
                },
                business_profile={"url": url, "mcc": "8398"},
                metadata=self.metadata,
            )

            self.account_id = account.id
            self.update(account)

        super().save(*args, **kwargs)

    @property
    def verification_link(self):
        stripe = get_stripe()

        account_link = stripe.AccountLink.create(
            account=self.account_id,
            refresh_url=f'{get_current_host()}/activities/stripe/expired',
            return_url=f'{get_current_host()}/activities/stripe/complete',
            type="account_onboarding",
            collection_options={
                "fields": "eventually_due",
                "future_requirements": "include",
            }
        )
        return account_link.url

    def update(self, data, save=True):
        self.requirements = data.requirements.eventually_due

        try:
            self.verified = data.individual.verification.status == "verified"
        except AttributeError:
            try:
                self.verified = (
                    data.company.owners_provided or
                    data.company.executives_provided or
                    data.company.directors_provided
                )
            except AttributeError:
                pass

        self.payments_enabled = data.charges_enabled
        self.payouts_enabled = data.payouts_enabled
        if self.id and save:
            self.save()

    def retrieve_account(self):
        try:
            stripe = get_stripe()
            account = stripe.Account.retrieve(self.account_id)
        except AuthenticationError:
            account = {}
        if not settings.LIVE_PAYMENTS_ENABLED and 'external_accounts' not in account:
            account = {}
        return account

    @cached_property
    def account(self):
        if not hasattr(self, '_account'):
            self._account = self.retrieve_account()
        return self._account

    @cached_property
    def name(self):
        if self.account.business_profile.name:
            return self.account.business_profile.name

        if self.account.individual.first_name:
            return f"{self.account.individual.first_name} {self.account.individual.last_name}"

        return self.owner.full_name

    def check_status(self):
        if self.account:
            del self.account
        self.update(self.account)

    class Meta(object):
        verbose_name = _('stripe payout account')
        verbose_name_plural = _('stripe payout accounts')

    class JSONAPIMeta(object):
        resource_name = 'payout-accounts/stripes'

    def __str__(self):
        return u"Stripe connect account {}".format(self.account_id)


@python_2_unicode_compatible
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

    @property
    def verified(self):
        return self.connect_account.verified

    @property
    def ready(self):
        return self.connect_account.verified

    @property
    def metadata(self):
        return {
            "tenant_name": connection.tenant.client_name,
            "tenant_domain": connection.tenant.domain_url,
        }

    class JSONAPIMeta(object):
        resource_name = 'payout-accounts/stripe-external-accounts'

    class Meta(object):
        verbose_name = _('Bank account')
        verbose_name_plural = _('Bank accounts')

    def __str__(self):
        return "Stripe external account {}".format(self.account_id)


from .states import *  # noqa
