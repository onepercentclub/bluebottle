from builtins import object
from adminsortable.admin import SortableAdmin
from django.contrib import admin
from django import forms
from django.db import connection
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from parler.admin import TranslatableAdmin
from parler.forms import TranslatableModelForm
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin
from tenant_schemas.postgresql_backend.base import FakeTenant

from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.statistics.models import (
    BaseStatistic, ManualStatistic, DatabaseStatistic, ImpactStatistic
)


class StatisticsChildAdmin(PolymorphicChildModelAdmin):
    list_display = ('name', 'active')
    readonly_fields = ('icon_preview',)
    base_model = BaseStatistic

    def icon_preview(self, obj):
        if not obj.icon:
            icon = 'default'
        else:
            icon = obj.icon
        return format_html(u'<img src="/goodicons/impact/{}-impact.svg">', icon)


class IconWidget(forms.RadioSelect):
    option_template_name = 'admin/impact/select_icon_option.html'
    template_name = 'admin/impact/select_icon.html'


class ManualStatisticForm(TranslatableModelForm):

    class Meta(object):
        model = ManualStatistic
        widgets = {
            'icon': IconWidget(),
        }
        fields = '__all__'


@admin.register(ManualStatistic)
class ManualStatisticChildAdmin(TranslatableAdmin, StatisticsChildAdmin):
    model = ManualStatistic
    form = ManualStatisticForm


@admin.register(DatabaseStatistic)
class DatabaseStatisticChildAdmin(TranslatableAdmin, StatisticsChildAdmin):
    model = DatabaseStatistic


@admin.register(ImpactStatistic)
class ImpactStatisticChildAdmin(StatisticsChildAdmin):
    model = ImpactStatistic


@admin.register(BaseStatistic)
class StatisticAdmin(SortableAdmin, PolymorphicParentModelAdmin):
    base_model = BaseStatistic
    list_display = ('name', 'statistics_type', 'active')
    list_editable = ('active', )
    child_models = (
        DatabaseStatistic,
        ManualStatistic,
        ImpactStatistic
    )

    def statistics_type(self, obj):
        return obj.get_real_instance_class()._meta.verbose_name
    statistics_type.short_description = _('Type')

    def get_child_models(self):
        if not isinstance(connection.tenant, FakeTenant):
            if not InitiativePlatformSettings.load().enable_impact:
                return tuple(x for x in self.child_models if x != ImpactStatistic)
        return self.child_models

    change_list_template = 'adminsortable/change_list_with_sort_link.html'

    def name(self, obj):
        for child in self.child_models:
            try:
                return getattr(obj, child.__name__.lower()).name
            except child.DoesNotExist:
                pass
        return obj
