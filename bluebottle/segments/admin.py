from django.contrib import admin
from django import forms
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from django.utils.html import format_html

from django_summernote.widgets import SummernoteWidget

from bluebottle.segments.models import SegmentType, Segment
from bluebottle.activities.models import Activity
from bluebottle.members.models import Member


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


class SegmentActivityInline(admin.TabularInline):
    model = Activity.segments.through
    fields = ('link', )
    readonly_fields = ('link', )
    extra = 0
    verbose_name = _('Activity')
    verbose_name_plural = _('Activities')

    def has_add_permission(self, request, obj=None):
        return False

    def link(self, obj):
        url = reverse('admin:activities_activity_change', args=(obj.activity.id, ))
        return format_html("<a href='{}'>{}</a>", url, obj.activity.title)


class SegmentMemberInline(admin.TabularInline):
    model = Member.segments.through
    fields = ('link', )
    readonly_fields = ('link', )
    extra = 0
    verbose_name = _('Member')
    verbose_name_plural = _('Members')

    def has_add_permission(self, request, obj=None):
        return False

    def link(self, obj):
        url = reverse('admin:members_member_change', args=(obj.member.id, ))
        return format_html("<a href='{}'>{}</a>", url, obj.member)


@admin.register(Segment)
class SegmentAdmin(admin.ModelAdmin):
    model = Segment
    form = SegmentAdminForm

    readonly_fields = ('text_color', )
    inlines = [SegmentActivityInline, SegmentMemberInline]

    list_display = ['name', 'slug']
    fieldsets = (
        (None, {
            'fields': ['name', 'slug']
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
