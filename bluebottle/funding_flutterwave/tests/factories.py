import factory

from bluebottle.funding.tests.factories import DonationFactory
from bluebottle.funding_flutterwave.models import FlutterwavePayment, FlutterwavePaymentProvider


class FlutterwavePaymentFactory(factory.DjangoModelFactory):

    donation = factory.SubFactory(DonationFactory)

    class Meta(object):
        model = FlutterwavePayment


class FlutterwavePaymentProviderFactory(factory.DjangoModelFactory):

    pub_key = 'fyi'
    sec_key = 'sssht'

    class Meta(object):
        model = FlutterwavePaymentProvider
