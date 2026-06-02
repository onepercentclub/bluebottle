from builtins import object

import factory.fuzzy
import mock
import munch

from bluebottle.funding.tests.factories import DonorFactory
from bluebottle.funding_stripe.models import (
    PaymentIntent, StripeSourcePayment,
    StripePayment, StripePayoutAccount,
    ExternalAccount, StripePaymentProvider
)
from bluebottle.funding_stripe.utils import get_stripe
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class StripeSourcePaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = StripeSourcePayment

    donation = factory.SubFactory(DonorFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        stripe = get_stripe()
        source_payment = stripe.Source(kwargs.get('souce_id', 'some source id'))
        source_payment.update({
            'client_secret': 'some client secret',
        })
        with mock.patch('stripe.Source.modify', return_value=source_payment):
            return super(StripeSourcePaymentFactory, cls)._create(model_class, *args, **kwargs)


class StripePaymentIntentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = PaymentIntent

    donation = factory.SubFactory(DonorFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        stripe = get_stripe()
        payment_intent = stripe.PaymentIntent(kwargs.get('intent_id', 'some intent id'))

        payment_intent.update({
            'client_secret': kwargs.get('client_secret', 'some client secret'),
        })
        with mock.patch('stripe.PaymentIntent.create', return_value=payment_intent):
            return super(StripePaymentIntentFactory, cls)._create(model_class, *args, **kwargs)


class StripePaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = StripePayment

    donation = factory.SubFactory(DonorFactory)
    payment_intent = factory.SubFactory(StripePaymentIntentFactory, donation=factory.SelfAttribute('..donation'))


class StripePayoutAccountFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = StripePayoutAccount

    country = 'NL'

    owner = factory.SubFactory(BlueBottleUserFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        if not StripePaymentProvider.objects.exists():
            StripePaymentProviderFactory.create()

        stripe = get_stripe()
        stripe_account_id = kwargs.get('account_id') or 'acct_1234567890'
        account = stripe.Account(id=stripe_account_id)
        account.business_type = "individual"
        account.individual = munch.munchify({
            "email": "test@example.com",
            "requirements": {
                "eventually_due": []
            }
        })
        account.requirements = munch.munchify({
            'eventually_due': [
                'individual.first_name', 'individual.last_name'
            ]
        })
        account.charges_enabled = True
        account.payouts_enabled = True
        account.business_profile = munch.munchify({
            "mcc": "8398",
            "product_description": "Not applicable - test factory account.",
            "url": "https://goodup.com",
        })
        account.email = "factory-stripe-account@example.com"
        account.company = None

        country_code = kwargs.get('country', 'NL')
        country_spec = stripe.CountrySpec(country_code)
        country_spec.update({
            "supported_bank_account_currencies": ['EUR'],
        })

        with mock.patch('stripe.Account.create', return_value=account), mock.patch(
            'stripe.Account.retrieve', return_value=account
        ), mock.patch(
            'stripe.Account.modify', return_value=account
        ), mock.patch(
            'stripe.CountrySpec.retrieve', return_value=country_spec
        ):
            return super(StripePayoutAccountFactory, cls)._create(model_class, *args, **kwargs)


class ExternalAccountFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = ExternalAccount

    connect_account = factory.SubFactory(StripePayoutAccountFactory)


class StripePaymentProviderFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = StripePaymentProvider
