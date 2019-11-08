import factory

from bluebottle.funding.tests.factories import DonationFactory
from bluebottle.funding_flutterwave.models import FlutterwavePayment, FlutterwavePaymentProvider, FlutterwaveBankAccount


class FlutterwavePaymentFactory(factory.DjangoModelFactory):

    donation = factory.SubFactory(DonationFactory)

    class Meta(object):
        model = FlutterwavePayment


class FlutterwavePaymentProviderFactory(factory.DjangoModelFactory):

    pub_key = 'fyi'
    sec_key = 'sssht'

    class Meta(object):
        model = FlutterwavePaymentProvider


class FlutterwaveBankAccountFactory(factory.DjangoModelFactory):

    account_number = factory.fuzzy.FuzzyInteger(10000, 99999)
    account_holder_name = 'Test Name'
    bank_country_code = 'NG'
    bank_code = '044'
    account = 'FW-123456'

    class Meta(object):
        model = FlutterwaveBankAccount
