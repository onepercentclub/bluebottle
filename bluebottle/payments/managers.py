from polymorphic.manager import PolymorphicManager


class PaymentManager(PolymorphicManager):
    def get_queryset(self):
        return super(PaymentManager, self).get_queryset()
