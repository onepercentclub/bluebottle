from django import forms
from django.contrib import admin
from django.db import connection
from django.forms.models import ModelFormMetaclass
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from django_summernote.widgets import SummernoteWidget

from bluebottle.fsm.forms import StateMachineModelFormMetaClass
from bluebottle.segments.models import SegmentType, Segment


class SegmentStateMachineModelFormMetaClass(StateMachineModelFormMetaClass):
    def __new__(cls, name, bases, attrs):
        if connection.tenant.schema_name != 'public':
            for field in SegmentType.objects.all():
                attrs[field.field_name] = forms.CharField(
                    required=False,
                    label=field.name
                )

        return super(SegmentStateMachineModelFormMetaClass, cls).__new__(cls, name, bases, attrs)


class SegmentAdminFormMetaClass(ModelFormMetaclass):
    def __new__(cls, name, bases, attrs):
        if connection.tenant.schema_name != 'public':
            for field in SegmentType.objects.all():
                attrs[field.field_name] = forms.CharField(
                    required=False,
                    label=field.name
                )

        return super(SegmentAdminFormMetaClass, cls).__new__(cls, name, bases, attrs)


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
class SegmentAdmin(admin.ModelAdmin, DynamicArrayMixin):
    model = Segment
    form = SegmentAdminForm

    readonly_fields = ('text_color', 'activities_link', 'members_link', 'type_link')

    list_display = ['name', 'segment_type', 'activities_link', ]

    list_filter = ['segment_type']
    search_fields = ['name']
    fieldsets = (
        (None, {
            'fields': [
                'type_link', 'name', 'slug', 'email_domains', 'closed',
                'activities_link', 'members_link'
            ]
        }),

        (_('Content'), {
            'fields': [
                'tag_line', 'story', 'background_color', 'text_color', 'logo', 'cover_image',
            ],
        }),

        (_('SSO'), {
            'fields': ['alternate_names'],
        }),
    )

    def has_add_permission(self, *args, **kwargs):
        return False

    def activities_link(self, obj):
        url = "{}?segments__id__exact={}".format(reverse('admin:activities_activity_changelist'), obj.id)
        return format_html("<a href='{}'>{} activities</a>", url, obj.activities.count())

    activities_link.short_description = _('Activities')

    def members_link(self, obj):
        url = "{}?segments__id__exact={}".format(reverse('admin:members_member_changelist'), obj.id)
        return format_html("<a href='{}'>{} members</a>", url, obj.users.count())

    members_link.short_description = _('Members')

    def type_link(self, obj):
        url = "{}".format(reverse('admin:segments_segmenttype_change', args=(obj.segment_type.pk, )))
        return format_html("<a href='{}'>{}</a>", url, obj.segment_type.name)

    type_link.short_description = _('Segment type')

    def text_color(self, obj):
        return obj.text_color

    text_color.short_description = _("Text colour")


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
