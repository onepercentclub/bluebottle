from adminsortable.admin import SortableAdmin
from django.contrib import admin
from django.db import connection
from django import forms
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from parler.admin import TranslatableAdmin
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

    def response_add(self, request, obj, post_url_continue=None):
        return redirect(reverse('admin:statistics_basestatistic_changelist'))

    def response_change(self, request, obj):
        return redirect(reverse('admin:statistics_basestatistic_changelist'))

    def response_delete(self, request, obj_display, obj_id):
        return redirect(reverse('admin:statistics_basestatistic_changelist'))

    def icon_preview(self, obj):
        if not obj.icon:
            return '-'
        return format_html(u'<img src="/goodicons/impact/{}-impact.svg">', obj.icon)


class IconWidget(forms.RadioSelect):
    option_template_name = 'admin/impact/select_icon_option.html'
    template_name = 'admin/impact/select_icon.html'


class ManualStatisticForm(forms.ModelForm):

    class Meta:
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
    list_display = ('name', 'polymorphic_ctype', 'active')
    list_editable = ('active', )
    child_models = (
        DatabaseStatistic,
        ManualStatistic,
        ImpactStatistic
    )

    def get_child_models(self):
        if not isinstance(connection.tenant, FakeTenant):
            if not InitiativePlatformSettings.load().enable_impact:
                return tuple(x for x in self.child_models if x != ImpactStatistic)
        return self.child_models

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
