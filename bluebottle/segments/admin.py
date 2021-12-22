from django.contrib import admin
from django import forms
from django.utils.translation import gettext_lazy as _
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin

from django_summernote.widgets import SummernoteWidget

from bluebottle.segments.models import SegmentType, Segment


class SegmentInline(admin.TabularInline):
    model = Segment
    fields = ('name', 'slug')
    show_change_link = True

    extra = 0


class SegmentAdminForm(forms.ModelForm):
    class Meta(object):
        model = Segment
        fields = '__all__'
        widgets = {
            'story': SummernoteWidget(attrs={'height': 400})
        }


@admin.register(Segment)
class SegmentAdmin(admin.ModelAdmin):
    model = Segment
    form = SegmentAdminForm

    readonly_fields = ('text_color', )

    list_display = ['name', 'slug']
    fieldsets = (
        (None, {
            'fields': ['name', 'slug']
        }),

        (_('Content'), {
            'fields': [
                'tag_line', 'story', 'background_color', 'text_color', 'logo', 'cover_image', 'closed',
            ],
        }),

        (_('SSO'), {
            'fields': ['alternate_names'],
        }),
    )


@admin.register(SegmentType)
class SegmentTypeAdmin(admin.ModelAdmin, DynamicArrayMixin):
    model = SegmentType
    inlines = [SegmentInline]

    def get_prepopulated_fields(self, request, obj=None):
        return {'slug': ('name',)}

    def segments(self, obj):
        return obj.segments.count()

    segments.short_description = _('Number of segments')

    list_display = ['name', 'slug', 'segments', 'is_active']
    list_editable = ['is_active']
