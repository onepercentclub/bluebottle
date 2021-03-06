from builtins import object
import factory

from bluebottle.funding.tests.factories import DonorFactory, PlainPayoutAccountFactory
from bluebottle.funding_flutterwave.models import FlutterwavePayment, FlutterwavePaymentProvider, FlutterwaveBankAccount


class FlutterwavePaymentFactory(factory.DjangoModelFactory):

    donation = factory.SubFactory(DonorFactory)
    tx_ref = factory.Sequence(lambda n: 'uid-{0}'.format(n))

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
    reviewed = True
    connect_account = factory.SubFactory(PlainPayoutAccountFactory)

    class Meta(object):
        model = FlutterwaveBankAccount
