from builtins import object
import factory.fuzzy

from bluebottle.funding.tests.factories import DonationFactory, PlainPayoutAccountFactory
from bluebottle.funding_vitepay.models import (
    VitepayPayment, VitepayPaymentProvider, VitepayBankAccount
)


class VitepayPaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = VitepayPayment

    donation = factory.SubFactory(DonationFactory)


class VitepayPaymentProviderFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = VitepayPaymentProvider

    api_secret = '123456789012345678901234567890123456789012345678901234567890'
    api_key = '12345'


class VitepayBankAccountFactory(factory.DjangoModelFactory):
    reviewed = True
    connect_account = factory.SubFactory(PlainPayoutAccountFactory)

    class Meta(object):
        model = VitepayBankAccount
