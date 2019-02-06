from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import CountryFactory
import factory

from bluebottle.payouts.models import (
    PayoutAccount, PlainPayoutAccount,
    PayoutDocument, StripePayoutAccount
)


class PayoutAccountFactory(factory.DjangoModelFactory):
    user = factory.SubFactory(BlueBottleUserFactory)

    class Meta(object):
        model = PayoutAccount


class PlainPayoutAccountFactory(factory.DjangoModelFactory):
    user = factory.SubFactory(BlueBottleUserFactory)

    account_holder_country = factory.SubFactory(CountryFactory)
    account_bank_country = factory.SubFactory(CountryFactory)

    class Meta(object):
        model = PlainPayoutAccount


class PayoutDocumentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = PayoutDocument


class StripePayoutAccountFactory(factory.DjangoModelFactory):
    user = factory.SubFactory(BlueBottleUserFactory)
    account_id = factory.Sequence(lambda n: 'acct_0000000{0}'.format(n))

    class Meta(object):
        model = StripePayoutAccount
