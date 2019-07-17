import factory.fuzzy

from bluebottle.funding.tests.factories import DonationFactory
from bluebottle.funding_vitepay.models import VitepayPayment, VitepayPaymentProvider


class VitepayPaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = VitepayPayment

    donation = factory.SubFactory(DonationFactory)


class VitepayPaymentProviderFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = VitepayPaymentProvider

    api_secret = '123456789012345678901234567890123456789012345678901234567890'
    api_key = '12345'
