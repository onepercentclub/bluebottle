from django.contrib import admin
from parler.admin import TranslatableAdmin

from bluebottle.impact.models import ImpactType, ImpactGoal


class ImpactGoalInline(admin.TabularInline):
    model = ImpactGoal
    extra = 0
    fields = ('type', 'target', 'realized')


class ImpactTypeAdmin(TranslatableAdmin):
    list_display = admin.ModelAdmin.list_display + ('name', 'active')

    def get_prepopulated_fields(self, request, obj=None):
        return {'slug': ('name',)}

    fields = (
        'name', 'slug', 'unit', 'active',
        'icon', 'text', 'text_with_target',
        'text_passed', 'text_passed_with_value',
    )


admin.site.register(ImpactType, ImpactTypeAdmin)
