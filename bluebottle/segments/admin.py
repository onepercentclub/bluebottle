from django.contrib import admin

from bluebottle.segments.models import SegmentType, Segment
from django.utils.translation import ugettext_lazy as _


class SegmentInline(admin.TabularInline):
    model = Segment

    extra = 0


@admin.register(SegmentType)
class SegmentAdmin(admin.ModelAdmin):
    model = SegmentType
    inlines = [SegmentInline]

    def get_prepopulated_fields(self, request, obj=None):
        return {'slug': ('name',)}

    def segments(self, obj):
        return obj.segments.count()
    segments.short_description = _('Number of segments')

    list_display = ['name', 'slug', 'segments', 'is_active']
    list_editable = ['is_active']
