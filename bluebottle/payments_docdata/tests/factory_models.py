import factory
from ..models import DocdataPayment, DocdataTransaction


class DocdataPaymentFactory(factory.DjangoModelFactory):
    FACTORY_FOR = DocdataPayment


class DocdataTransactionFactory(factory.DjangoModelFactory):
    FACTORY_FOR = DocdataTransaction

