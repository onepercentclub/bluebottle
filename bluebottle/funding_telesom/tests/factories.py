from builtins import object
import factory.fuzzy

from bluebottle.funding.tests.factories import DonationFactory
from bluebottle.funding_telesom.models import (
    TelesomPayment, TelesomPaymentProvider, TelesomBankAccount
)


class TelesomPaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = TelesomPayment

    donation = factory.SubFactory(DonationFactory)


class TelesomPaymentProviderFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = TelesomPaymentProvider

    merchant_uid = '1234567890'
    api_key = '12345'
    api_user_id = '1000'


class TelesomBankAccountFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = TelesomBankAccount
