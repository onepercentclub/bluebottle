from adminsortable.admin import SortableAdmin
from django.contrib import admin
from parler.admin import TranslatableAdmin
from polymorphic.admin import PolymorphicParentModelAdmin

from bluebottle.statistics.models import (
    BaseStatistic, ManualStatistic, DatabaseStatistic, ImpactStatistic
)


@admin.register(ManualStatistic)
class ManualStatisticChildAdmin(TranslatableAdmin):
    model = ManualStatistic
    list_editable = ('active', )
    list_display = ('name', 'active')


@admin.register(DatabaseStatistic)
class DatabaseStatisticChildAdmin(TranslatableAdmin):
    model = DatabaseStatistic
    list_editable = ('active', )
    list_display = ('name', 'active')


@admin.register(ImpactStatistic)
class ImpactStatisticChildAdmin(admin.ModelAdmin):
    model = ImpactStatistic
    raw_id_fields = ['impact_type']


@admin.register(BaseStatistic)
class StatisticAdmin(SortableAdmin, PolymorphicParentModelAdmin):
    base_model = BaseStatistic
    list_display = ('sequence', 'name', 'polymorphic_ctype', 'active')
    list_editable = ('active',)
    child_models = (
        DatabaseStatistic,
        ManualStatistic,
        ImpactStatistic
    )

    # We need this because Django Polymorphic uses a calculated property to
    # override change_list_template instead of using get_changelist_template.
    # adminsortable tries to set that value and then fails.
    _change_list_template = 'adminsortable/change_list_with_sort_link.html'

    @property
    def change_list_template(self):
        return self._change_list_template

    @change_list_template.setter
    def change_list_template(self, value):
        self._change_list_template = value

    def name(self, obj):
        for child in self.child_models:
            try:
                return getattr(obj, child.__name__.lower()).name
            except child.DoesNotExist:
                pass
        return obj
