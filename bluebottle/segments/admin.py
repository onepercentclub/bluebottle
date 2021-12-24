from django.contrib import admin
from django import forms
from django.urls import reverse
from django.utils.html import format_html
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

    readonly_fields = ('text_color', 'activities_link', 'show_in_frontend')

    list_display = ['name', 'segment_type', 'activities_link', 'show_in_frontend']

    list_filter = ['segment_type']
    search_fields = ['name']
    fieldsets = (
        (None, {
            'fields': ['name', 'slug', 'activities_link']
        }),

        (_('Content'), {
            'fields': [
                'tag_line', 'story', 'background_color', 'text_color', 'logo', 'cover_image'
            ],
        }),

        (_('SSO'), {
            'fields': ['alternate_names'],
        }),
    )

    def activities_link(self, obj):
        url = "{}?segments__id__exact={}".format(reverse('admin:activities_activity_changelist'), obj.id)
        return format_html("<a href='{}'>{} activities</a>".format(url, obj.activities.count()))

    def show_in_frontend(self, obj):
        return format_html(
            "<a href='{}'>{}</a>",
            obj.get_absolute_url(),
            _('View on site')
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
