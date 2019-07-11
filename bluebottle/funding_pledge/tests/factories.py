import factory.fuzzy

from bluebottle.funding.tests.factories import DonationFactory
from bluebottle.funding_pledge.models import PledgePayment


class PledgePaymentFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = PledgePayment

    donation = factory.SubFactory(DonationFactory)
