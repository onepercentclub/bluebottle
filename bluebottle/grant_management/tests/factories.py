from builtins import object
from moneyed import Money

import factory

from bluebottle.test.factory_models import generate_rich_text

from bluebottle.grant_management.models import (
    GrantApplication, GrantDonor, GrantFund, GrantDeposit, GrantPayment
)
from bluebottle.test.factory_models.projects import ThemeFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


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


class GrantDonorFactory(factory.DjangoModelFactory):
    class Meta:
        model = GrantDonor

    amount = Money(5000, 'EUR')


class GrantFundFactory(factory.DjangoModelFactory):
    class Meta:
        model = GrantFund


class GrantDepositFactory(factory.DjangoModelFactory):
    class Meta:
        model = GrantDeposit

    amount = Money(5000, 'EUR')


class GrantPaymentFactory(factory.DjangoModelFactory):
    class Meta:
        model = GrantPayment

    total = Money(5000, 'EUR')
