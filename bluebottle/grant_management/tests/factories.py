import factory
from builtins import object
from moneyed import Money

from bluebottle.grant_management.models import (
    GrantApplication, GrantDonor, GrantFund, GrantDeposit, GrantWithdrawal, GrantPayment
)
from bluebottle.grant_management.models import (
    GrantProvider, GrantPayout
)
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models import generate_rich_text
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ThemeFactory


class GrantApplicationFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = GrantApplication

    title = factory.Faker('sentence')
    slug = factory.Faker('slug')
    description = factory.LazyFunction(generate_rich_text)

    owner = factory.SubFactory(BlueBottleUserFactory)
    initiative = factory.SubFactory(InitiativeFactory)
    target = Money(5000, 'EUR')
    theme = factory.SubFactory(ThemeFactory)


class GrantProviderFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = GrantProvider

    name = factory.Faker('sentence')
    description = factory.LazyFunction(generate_rich_text)
    payment_frequency = 1
    stripe_customer_id = factory.Faker('uuid4')
    owner = factory.SubFactory(BlueBottleUserFactory)


class GrantFundFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = GrantFund

    name = factory.Faker('sentence')
    currency = 'EUR'
    description = factory.LazyFunction(generate_rich_text)
    grant_provider = factory.SubFactory(GrantProviderFactory)


class GrantPayoutFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = GrantPayout

    activity = factory.SubFactory(GrantApplicationFactory)
    provider = 'stripe'
    currency = 'EUR'
    status = 'approved'


class GrantDonorFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = GrantDonor

    activity = factory.SubFactory(GrantApplicationFactory)
    fund = factory.SubFactory(GrantFundFactory)
    amount = Money(5000, 'EUR')
    payout = factory.SubFactory(GrantPayoutFactory)


class GrantDepositFactory(factory.DjangoModelFactory):
    class Meta:
        model = GrantDeposit

    amount = Money(5000, 'EUR')


class GrantWithdrawalFactory(factory.DjangoModelFactory):
    class Meta:
        model = GrantWithdrawal

    amount = Money(5000, 'EUR')


class GrantPaymentFactory(factory.DjangoModelFactory):
    class Meta:
        model = GrantPayment

    grant_provider = factory.SubFactory(GrantProviderFactory)
