import factory.fuzzy

from bluebottle.funding.tests.factories import DonationFactory
from bluebottle.funding_stripe.models import (
    PaymentIntent, StripeSourcePayment,
    StripePayment, StripePayoutAccount,
    ExternalAccount, StripePaymentProvider
)
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

    country = factory.Faker('country_code')

    owner = factory.SubFactory(BlueBottleUserFactory)


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
