import factory.fuzzy
from moneyed import Money
from pytz import UTC

from bluebottle.funding.models import (
    Funding, Donation, Reward, BudgetLine, Payment, BankAccount,
    PlainPayoutAccount, Payout
)
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class FundingFactory(factory.DjangoModelFactory):
    class Meta:
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
    class Meta:
        model = Donation

    activity = factory.SubFactory(FundingFactory)
    user = factory.SubFactory(BlueBottleUserFactory)
    amount = Money(35, 'EUR')


class PaymentFactory(factory.DjangoModelFactory):
    class Meta:
        model = Payment

    activity = factory.SubFactory(FundingFactory)
    user = factory.SubFactory(BlueBottleUserFactory)
    amount = Money(35, 'EUR')


class RewardFactory(factory.DjangoModelFactory):
    activity = factory.SubFactory(FundingFactory)
    amount = Money(35, 'EUR')

    class Meta:
        model = Reward


class BudgetLineFactory(factory.DjangoModelFactory):
    amount = Money(35, 'EUR')
    activity = factory.SubFactory(FundingFactory)

    class Meta:
        model = BudgetLine


class PlainPayoutAccountFactory(factory.DjangoModelFactory):
    owner = factory.SubFactory(BlueBottleUserFactory)
    reviewed = True

    class Meta:
        model = PlainPayoutAccount


class BankAccountFactory(factory.DjangoModelFactory):
    reviewed = True
    connect_account = factory.SubFactory(PlainPayoutAccountFactory)

    class Meta:
        model = BankAccount


class PayoutFactory(factory.DjangoModelFactory):
    activity = factory.SubFactory(FundingFactory)

    class Meta:
        model = Payout
