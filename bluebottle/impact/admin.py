from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from parler.admin import TranslatableAdmin

from bluebottle.impact.models import ImpactType, ImpactGoal
from bluebottle.utils.admin import TranslatableAdminOrderingMixin


class ImpactGoalInline(admin.TabularInline):
    model = ImpactGoal
    extra = 0
    readonly_fields = ('unit', 'realized_from_contributions', )
    fields = ('type', 'target', 'unit', 'realized', 'realized_from_contributions', )

    def unit(self, obj):
        return obj.type.unit
    unit.short_description = _('Unit')


class ImpactTypeAdmin(TranslatableAdminOrderingMixin, TranslatableAdmin):
    list_display = admin.ModelAdmin.list_display + ('name', 'active')

    def get_prepopulated_fields(self, request, obj=None):
        return {'slug': ('name',)}

    fields = (
        'name', 'slug', 'unit', 'active',
        'icon', 'text', 'text_with_target',
        'text_passed',
    )


admin.site.register(ImpactType, ImpactTypeAdmin)
