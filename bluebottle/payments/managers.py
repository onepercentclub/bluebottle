from polymorphic import PolymorphicManager


class PaymentManager(PolymorphicManager):
    def get_query_set(self):
        return super(PaymentManager, self).get_query_set()
