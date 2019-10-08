import factory.fuzzy
from moneyed import Money
from pytz import UTC

from bluebottle.funding.models import (
    Funding, Donation, Reward, Fundraiser, BudgetLine, Payment, BankAccount
)
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class BankAccountFactory(factory.DjangoModelFactory):
    reviewed = True

    class Meta(object):
        model = BankAccount


class FundingFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Funding

    title = factory.Faker('sentence')
    slug = factory.Faker('slug')
    description = factory.Faker('text')

    owner = factory.SubFactory(BlueBottleUserFactory)
    initiative = factory.SubFactory(InitiativeFactory)
    deadline = factory.Faker('future_datetime', tzinfo=UTC)
    target = Money(5000, 'EUR')
    amount_matching = Money(0, 'EUR')


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

    amount = Money(3500, 'EUR')
    activity = factory.SubFactory(FundingFactory)
    owner = factory.SubFactory(BlueBottleUserFactory)


class BudgetLineFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = BudgetLine

    activity = factory.SubFactory(FundingFactory)
