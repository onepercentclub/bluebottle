import factory.fuzzy

from bluebottle.funding_stripe.models import (
    StripePayment, ConnectAccount, ExternalAccount
)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.funding.tests.factories import DonationFactory


class StripePaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = StripePayment

    donation = factory.SubFactory(DonationFactory)


class ConnectAccountFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = ConnectAccount

    country = factory.Faker('country_code')

    owner = factory.SubFactory(BlueBottleUserFactory)


class ExternalAccountFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = ExternalAccount

    connect_account = factory.SubFactory(ConnectAccount)
