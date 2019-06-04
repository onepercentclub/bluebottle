import factory.fuzzy

from bluebottle.funding.models import Funding, Donation
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.payouts import StripePayoutAccountFactory


class FundingFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Funding

    title = factory.Faker('sentence')
    description = factory.Faker('text')

    owner = factory.SubFactory(BlueBottleUserFactory)
    initiative = factory.SubFactory(InitiativeFactory)
    account = factory.SubFactory(StripePayoutAccountFactory)
    target = 100


class DonationFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Donation

    activity = factory.SubFactory(FundingFactory)
    user = factory.SubFactory(BlueBottleUserFactory)
