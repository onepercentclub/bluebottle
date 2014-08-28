from django.db import models

from polymorphic import PolymorphicManager

from bluebottle.utils.managers import GenericForeignKeyManagerMixin


class PaymentLogManager(GenericForeignKeyManagerMixin):
    def get_query_set(self):
        return super(PaymentLogManager, self).get_query_set()
