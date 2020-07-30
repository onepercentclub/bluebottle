from adminsortable.admin import SortableAdmin
from django.contrib import admin
from django.utils.html import format_html
from parler.admin import TranslatableAdmin
from polymorphic.admin import PolymorphicParentModelAdmin

from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.statistics.models import (
    BaseStatistic, ManualStatistic, DatabaseStatistic, ImpactStatistic
)


@admin.register(ManualStatistic)
class ManualStatisticChildAdmin(TranslatableAdmin):
    model = ManualStatistic
    list_editable = ('active', )
    list_display = ('name', 'active')
    readonly_fields = ('icon_preview',)

    def icon_preview(self, obj):
        if not obj.icon:
            return '-'
        return format_html(u'<img src="/goodicons/impact/{}-impact.svg">', obj.icon)


@admin.register(DatabaseStatistic)
class DatabaseStatisticChildAdmin(TranslatableAdmin):
    model = DatabaseStatistic
    list_editable = ('active', )
    list_display = ('name', 'active')
    readonly_fields = ('icon_preview',)

    def icon_preview(self, obj):
        if not obj.icon:
            return '-'
        return format_html(u'<img src="/goodicons/impact/{}-impact.svg">', obj.icon)


@admin.register(ImpactStatistic)
class ImpactStatisticChildAdmin(admin.ModelAdmin):
    model = ImpactStatistic
    raw_id_fields = ['impact_type']
    readonly_fields = ('icon_preview',)

    def icon_preview(self, obj):
        if not obj.icon:
            return '-'
        return format_html(u'<img src="/goodicons/impact/{}-impact.svg">', obj.icon)


@admin.register(BaseStatistic)
class StatisticAdmin(SortableAdmin, PolymorphicParentModelAdmin):
    base_model = BaseStatistic
    list_display = ('sequence', 'name', 'polymorphic_ctype', 'active')
    list_editable = ('active',)
    child_models = (
        DatabaseStatistic,
        ManualStatistic
    )
    _child_models = child_models

    def get_child_models(self):
        # Make sure we can dynamically add
        return self._child_models

    def get_child_type_choices(self, request, action):
        if InitiativePlatformSettings.load().enable_impact:
            self._child_models += (ImpactStatistic,)
        return super(StatisticAdmin, self).get_child_type_choices(request, action)

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
