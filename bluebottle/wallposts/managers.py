from django.db import models

from polymorphic.manager import PolymorphicManager

from bluebottle.utils.managers import GenericForeignKeyManagerMixin


class WallpostManager(GenericForeignKeyManagerMixin, PolymorphicManager):
    def get_queryset(self):
        queryset = super(WallpostManager, self).get_queryset()
        return queryset.filter(deleted__isnull=True)


class ReactionManager(models.Manager):
    def get_queryset(self):
        queryset = super(ReactionManager, self).get_queryset()
        return queryset.filter(deleted__isnull=True)
