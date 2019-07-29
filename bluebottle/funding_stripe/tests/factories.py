import factory.fuzzy

from bluebottle.funding_stripe.models import (
    StripePayment, StripePayoutAccount, ExternalAccount, StripePaymentProvider
)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.funding.tests.factories import DonationFactory


class StripePaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = StripePayment

    donation = factory.SubFactory(DonationFactory)


class ConnectAccountFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = StripePayoutAccount

    country = factory.Faker('country_code')

    owner = factory.SubFactory(BlueBottleUserFactory)


class ExternalAccountFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = ExternalAccount

    connect_account = factory.SubFactory(StripePayoutAccount)


class StripePaymentProviderFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = StripePaymentProvider

    credit_card = True
    ideal = True
    bancontact = True
    direct_debit = True
