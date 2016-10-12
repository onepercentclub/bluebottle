import factory
from ..models import InterswitchPayment


class InterswitchPaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = InterswitchPayment
