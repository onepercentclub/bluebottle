from django.contrib import admin
from parler.admin import TranslatableAdmin

from bluebottle.impact.models import ImpactType, ImpactGoal


class ImpactGoalInline(admin.TabularInline):
    model = ImpactGoal
    extra = 0
    fields = ('type', 'target', 'realized')


class ImpactTypeAdmin(TranslatableAdmin):
    list_display = admin.ModelAdmin.list_display + ('name', 'active')
    fields = (
        'slug', 'name', 'unit', 'active',
        'text', 'text_with_target',
        'text_passed', 'text_passed_with_value',
    )


admin.site.register(ImpactType, ImpactTypeAdmin)
