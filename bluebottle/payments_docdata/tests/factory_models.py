import factory
from ..models import DocdataPayment, DocdataTransaction, \
    DocdataDirectdebitPayment


class DocdataPaymentFactory(factory.DjangoModelFactory):
    FACTORY_FOR = DocdataPayment


class DocdataDirectdebitPaymentFactory(factory.DjangoModelFactory):
    FACTORY_FOR = DocdataDirectdebitPayment


class DocdataTransactionFactory(factory.DjangoModelFactory):
    FACTORY_FOR = DocdataTransaction
