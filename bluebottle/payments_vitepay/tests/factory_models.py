import factory
from ..models import VitepayPayment


class VitepayPaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = VitepayPayment
