import factory.fuzzy

from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.funding.tests.factories import DonationFactory
from bluebottle.funding_pledge.models import (
    PledgePayment, PledgePaymentProvider, PledgeBankAccount
)


class PledgePaymentFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = PledgePayment

    donation = factory.SubFactory(DonationFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        payment = super(PledgePaymentFactory, cls)._create(model_class, *args, **kwargs)
        payment.transitions.succeed()
        payment.save()
        return payment


class PledgePaymentProviderFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = PledgePaymentProvider


class PledgeBankAccountFactory(factory.DjangoModelFactory):
    account_holder_name = factory.Faker('name')
    account_holder_address = factory.Faker('address')
    account_holder_postal_code = factory.Faker('postalcode')
    account_holder_city = factory.Faker('city')
    account_number = factory.Faker('bban')
    account_details = factory.Faker('sentence')

    account_holder_country = factory.SubFactory(CountryFactory)
    account_bank_country = factory.SubFactory(CountryFactory)

    class Meta(object):
        model = PledgeBankAccount
