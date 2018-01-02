import factory
from ..models import DocdataPayment, DocdataTransaction, \
    DocdataDirectdebitPayment


class DocdataPaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = DocdataPayment


class DocdataDirectdebitPaymentFactory(factory.DjangoModelFactory):
    total_gross_amount = 500.00

    class Meta(object):
        model = DocdataDirectdebitPayment


class DocdataTransactionFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = DocdataTransaction
