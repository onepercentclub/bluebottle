import factory.fuzzy

from bluebottle.funding.tests.factories import DonationFactory
from bluebottle.funding_vitepay.models import VitepayPayment


class VitepayPaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = VitepayPayment

    mobile_number = '77000001'
    donation = factory.SubFactory(DonationFactory)
