import factory.fuzzy

from bluebottle.funding.tests.factories import DonationFactory
from bluebottle.funding_lipisha.models import LipishaPayment
from bluebottle.funding_lipisha.models import LipishaPaymentProvider, LipishaBankAccount


class LipishaPaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = LipishaPayment
    donation = factory.SubFactory(DonationFactory)


class LipishaPaymentProviderFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = LipishaPaymentProvider

    api_signature = '123456789012345678901234567890123456789012345678901234567890'
    api_key = '12345'


class LipishaBankAccountFactory(factory.DjangoModelFactory):

    account_number = factory.fuzzy.FuzzyInteger(10000, 99999)

    class Meta(object):
        model = LipishaBankAccount
