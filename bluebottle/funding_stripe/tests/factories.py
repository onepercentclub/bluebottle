import factory.fuzzy

from bluebottle.funding_stripe.models import StripePayment
from bluebottle.funding.tests.factories import DonationFactory


class StripePaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = StripePayment

    donation = factory.SubFactory(DonationFactory)
