from django.db import models

from polymorphic import PolymorphicManager

from bluebottle.utils.managers import GenericForeignKeyManagerMixin


class WallpostManager(GenericForeignKeyManagerMixin, PolymorphicManager):
    def get_query_set(self):
        queryset = super(WallpostManager, self).get_query_set()
        return queryset.filter(deleted__isnull=True)


class ReactionManager(models.Manager):
    def get_query_set(self):
        queryset = super(ReactionManager, self).get_query_set()
        return queryset.filter(deleted__isnull=True)
