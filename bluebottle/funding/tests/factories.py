from builtins import object
import factory.fuzzy
from moneyed import Money
from pytz import UTC

from bluebottle.test.factory_models import generate_rich_text

from bluebottle.funding.models import (
    Funding, Donor, Reward, BudgetLine, Payment, BankAccount,
    PlainPayoutAccount, Payout
)
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class FundingFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Funding

    title = factory.Faker('sentence')
    slug = factory.Faker('slug')
    description = factory.LazyFunction(generate_rich_text)

    owner = factory.SubFactory(BlueBottleUserFactory)
    initiative = factory.SubFactory(InitiativeFactory)
    deadline = factory.Faker('future_datetime', tzinfo=UTC)
    target = Money(5000, 'EUR')
    amount_matching = Money(0, 'EUR')


class DonorFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Donor

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
    activity = factory.SubFactory(FundingFactory)
    amount = Money(35, 'EUR')

    class Meta(object):
        model = Reward


class BudgetLineFactory(factory.DjangoModelFactory):
    amount = Money(35, 'EUR')
    activity = factory.SubFactory(FundingFactory)

    class Meta(object):
        model = BudgetLine


class PlainPayoutAccountFactory(factory.DjangoModelFactory):
    owner = factory.SubFactory(BlueBottleUserFactory)
    reviewed = True

    class Meta(object):
        model = PlainPayoutAccount


class BankAccountFactory(factory.DjangoModelFactory):
    reviewed = True
    connect_account = factory.SubFactory(PlainPayoutAccountFactory)

    class Meta(object):
        model = BankAccount


class PayoutFactory(factory.DjangoModelFactory):
    activity = factory.SubFactory(FundingFactory)

    class Meta(object):
        model = Payout
