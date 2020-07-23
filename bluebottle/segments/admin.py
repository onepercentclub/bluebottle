from django.contrib import admin

from bluebottle.segments.models import SegmentType, Segment


class SegmentInline(admin.TabularInline):
    model = Segment

    extra = 0


@admin.register(SegmentType)
class SegmentAdmin(admin.ModelAdmin):
    model = SegmentType
    inlines = [SegmentInline]

    def get_prepopulated_fields(self, request, obj=None):
        return {'slug': ('name',)}

    list_display = ['name', 'slug']
