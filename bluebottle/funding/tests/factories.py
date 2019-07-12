import factory.fuzzy
from moneyed import Money

from bluebottle.funding.models import Funding, Donation, Reward, Fundraiser, BudgetLine, Payment
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.payouts import StripePayoutAccountFactory


class FundingFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Funding

    title = factory.Faker('sentence')
    slug = factory.Faker('slug')
    description = factory.Faker('text')

    owner = factory.SubFactory(BlueBottleUserFactory)
    initiative = factory.SubFactory(InitiativeFactory)
    account = factory.SubFactory(StripePayoutAccountFactory)
    deadline = factory.Faker('future_date')
    target = Money(5000, 'EUR')


class DonationFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Donation

    activity = factory.SubFactory(FundingFactory)
    user = factory.SubFactory(BlueBottleUserFactory)
    amount = Money(35, 'EUR')

    
class PaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Payment

    activity = factory.SubFactory(FundingFactory)
    user = factory.SubFactory(BlueBottleUserFactory)
    amount = Money(35, 'EUR')


class RewardFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Reward

    activity = factory.SubFactory(FundingFactory)


class FundraiserFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Fundraiser

    activity = factory.SubFactory(FundingFactory)
    owner = factory.SubFactory(BlueBottleUserFactory)


class BudgetLineFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = BudgetLine

    activity = factory.SubFactory(FundingFactory)
