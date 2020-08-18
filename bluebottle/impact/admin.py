from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from parler.admin import TranslatableAdmin

from bluebottle.impact.models import ImpactType, ImpactGoal


class ImpactGoalInline(admin.TabularInline):
    model = ImpactGoal
    extra = 0
    readonly_fields = ('unit', )
    fields = ('type', 'target', 'unit', 'realized')

    def unit(self, obj):
        return obj.type.unit
    unit.short_description = _('Unit')


class ImpactTypeAdmin(TranslatableAdmin):
    list_display = admin.ModelAdmin.list_display + ('text', 'active')

    def get_prepopulated_fields(self, request, obj=None):
        return {'slug': ('text',)}

    fields = (
        'slug', 'unit', 'active',
        'icon', 'text', 'text_with_target',
        'text_passed',
    )


admin.site.register(ImpactType, ImpactTypeAdmin)
