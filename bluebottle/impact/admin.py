from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from parler.admin import TranslatableAdmin

from bluebottle.impact.models import ImpactType, ImpactGoal
from bluebottle.utils.admin import TranslatableAdminOrderingMixin


class ImpactGoalInline(admin.TabularInline):
    model = ImpactGoal
    extra = 0
    readonly_fields = ('unit', 'realized_from_contributions', )
    fields = ('type', 'target', 'unit', 'realized', 'realized_from_contributions', 'participant_impact')

    def unit(self, obj):
        return obj.type.unit
    unit.short_description = _('Unit')


class ImpactTypeAdmin(TranslatableAdminOrderingMixin, TranslatableAdmin):
    list_display = admin.ModelAdmin.list_display + ('name', 'active', 'activities')

    def get_prepopulated_fields(self, request, obj=None):
        return {'slug': ('name',)}
    readonly_fields = ('activities',)

    fields = (
        'name', 'slug', 'unit', 'active',
        'icon', 'text', 'text_with_target',
        'text_passed', 'activities'
    )

    def activities(self, obj):
        url = reverse('admin:activities_activity_changelist')
        total = obj.goals.count()
        return format_html('<a href="{}?goals__type__id__exact={}">{} activities</a>', url, obj.id, total)


admin.site.register(ImpactType, ImpactTypeAdmin)
