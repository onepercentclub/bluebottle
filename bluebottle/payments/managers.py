from django.db import models

from polymorphic import PolymorphicManager

from bluebottle.utils.managers import GenericForeignKeyManagerMixin


class PaymentManager(PolymorphicManager):
    def get_query_set(self):
        return super(PaymentManager, self).get_query_set()
