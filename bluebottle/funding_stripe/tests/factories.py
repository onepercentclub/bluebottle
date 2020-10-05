from builtins import object
import factory.fuzzy
import munch
import mock

from bluebottle.funding.tests.factories import DonationFactory
from bluebottle.funding_stripe.models import (
    PaymentIntent, StripeSourcePayment,
    StripePayment, StripePayoutAccount,
    ExternalAccount, StripePaymentProvider
)
from bluebottle.funding_stripe.utils import stripe
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class StripeSourcePaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = StripeSourcePayment

    donation = factory.SubFactory(DonationFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        source_payment = stripe.Source(kwargs.get('souce_id', 'some source id'))
        source_payment.update({
            'client_secret': 'some client secret',
        })
        with mock.patch('stripe.Source.modify', return_value=source_payment):
            return super(StripeSourcePaymentFactory, cls)._create(model_class, *args, **kwargs)


class StripePaymentIntentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = PaymentIntent

    donation = factory.SubFactory(DonationFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        payment_intent = stripe.PaymentIntent(kwargs.get('intent_id', 'some intent id'))
        payment_intent.update({
            'client_secret': 'some client secret',
        })
        with mock.patch('stripe.PaymentIntent.create', return_value=payment_intent):
            return super(StripePaymentIntentFactory, cls)._create(model_class, *args, **kwargs)


class StripePaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = StripePayment

    donation = factory.SubFactory(DonationFactory)
    payment_intent = factory.SubFactory(StripePaymentIntentFactory, donation=factory.SelfAttribute('..donation'))


class StripePayoutAccountFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = StripePayoutAccount

    country = 'NL'

    owner = factory.SubFactory(BlueBottleUserFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        account_id = 'acct_1234567890'
        account = stripe.Account(
            id=account_id,
        )
        account.requirements = munch.munchify({
            'eventually_due': [
                'individual.first_name', 'individual.last_name'
            ]
        })

        with mock.patch('stripe.Account.create', return_value=account):
            return super(StripePayoutAccountFactory, cls)._create(model_class, *args, **kwargs)


class ExternalAccountFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = ExternalAccount

    connect_account = factory.SubFactory(StripePayoutAccountFactory)


class StripePaymentProviderFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = StripePaymentProvider

    credit_card = True
    ideal = True
    bancontact = True
    direct_debit = True
