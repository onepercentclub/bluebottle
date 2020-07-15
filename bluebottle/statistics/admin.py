from django.contrib import admin
from parler.admin import TranslatableAdmin

from polymorphic.admin import PolymorphicParentModelAdmin


from bluebottle.statistics.models import (
    BaseStatistic, ManualStatistic, DatabaseStatistic, ImpactStatistic
)


@admin.register(ManualStatistic)
class ManualStatisticChildAdmin(TranslatableAdmin):
    model = ManualStatistic


@admin.register(DatabaseStatistic)
class DatabaseStatisticChildAdmin(TranslatableAdmin):
    model = DatabaseStatistic


@admin.register(ImpactStatistic)
class ImpactStatisticChildAdmin(TranslatableAdmin):
    model = ImpactStatistic


@admin.register(BaseStatistic)
class StatisticAdmin(PolymorphicParentModelAdmin):
    base_model = BaseStatistic
    child_models = (DatabaseStatistic, ManualStatistic, ImpactStatistic)
