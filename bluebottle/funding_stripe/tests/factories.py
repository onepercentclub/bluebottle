import factory.fuzzy
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


class StripePaymentIntentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = PaymentIntent

    donation = factory.SubFactory(DonationFactory)


class StripePaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = StripePayment

    donation = factory.SubFactory(DonationFactory)
    payment_intent = factory.SubFactory(StripePaymentIntentFactory)


class StripePayoutAccountFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = StripePayoutAccount

    country = 'NL'

    owner = factory.SubFactory(BlueBottleUserFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        account_id = 'acct_1234567890'
        with mock.patch('stripe.Account.create', return_value=stripe.Account(id=account_id)):
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
