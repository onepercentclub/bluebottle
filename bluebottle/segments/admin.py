from django import forms
from django.contrib import admin
from django.db import connection
from django.forms.models import ModelFormMetaclass
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _, get_language
from django_admin_inline_paginator.admin import TabularInlinePaginated
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from parler.admin import TranslatableAdmin

from bluebottle.bluebottle_dashboard.admin import AdminMergeMixin
from bluebottle.fsm.forms import StateMachineModelFormMetaClass
from bluebottle.segments.models import SegmentType, Segment
from bluebottle.translations.admin import TranslatableLabelAdminMixin


class SegmentStateMachineModelFormMetaClass(StateMachineModelFormMetaClass):
    def __new__(cls, name, bases, attrs):
        if connection.tenant.schema_name != 'public':
            for field in SegmentType.objects.all():
                field_name = field.safe_translation_getter('name', field.slug)
                attrs[field.field_name] = forms.CharField(
                    required=False,
                    label=field_name
                )

        return super(SegmentStateMachineModelFormMetaClass, cls).__new__(cls, name, bases, attrs)


class SegmentAdminFormMetaClass(ModelFormMetaclass):
    def __new__(cls, name, bases, attrs):
        if connection.tenant.schema_name != 'public':
            for field in SegmentType.objects.all():
                field_name = field.safe_translation_getter('name', field.slug)
                attrs[field.field_name] = forms.CharField(
                    required=False,
                    label=field_name
                )

        return super(SegmentAdminFormMetaClass, cls).__new__(cls, name, bases, attrs)


class SegmentInline(TabularInlinePaginated):
    model = Segment
    fields = ('segment_name', 'slug')
    show_change_link = True
    can_delete = True
    readonly_fields = ('segment_name',)

    extra = 0

    def segment_name(self, obj):
        if obj and obj.pk:
            return obj.safe_translation_getter('name', obj.slug)
        return ''

    segment_name.short_description = _('Name')


class SegmentMergeForm(forms.Form):
    to = forms.ModelChoiceField(
        label=_("Merge with"),
        help_text=_("Choose location to merge with"),
        queryset=Segment.objects.all(),
    )

    title = _("Merge")

    def __init__(self, obj, *args, **kwargs):
        super(SegmentMergeForm, self).__init__(*args, **kwargs)

        self.fields["to"].queryset = (
            self.fields["to"]
            .queryset.exclude(pk=obj.pk)
            .filter(segment_type=obj.segment_type)
        )


@admin.register(Segment)
class SegmentAdmin(
    TranslatableLabelAdminMixin, TranslatableAdmin,
    AdminMergeMixin, admin.ModelAdmin,
    DynamicArrayMixin
):
    model = Segment

    readonly_fields = ('translatable_info', 'text_color', 'activities_link', 'members_link', 'type_link')

    list_display = ['name', 'segment_type', 'activities_link', ]

    list_filter = ['segment_type']
    search_fields = ['translations__name']
    fieldsets = (
        (None, {
            'fields': [
                'translatable_info',
                'type_link', 'name', 'slug', 'email_domains', 'closed',
                'activities_link', 'members_link'
            ]
        }),

        (_('Content'), {
            'fields': [
                'slogan', 'story', 'logo', 'cover_image',
                'background_color', 'text_color',
                'button_color', 'button_text_color'
            ],
        }),

        (_('SSO'), {
            'fields': ['alternate_names'],
        }),
    )

    merge_form = SegmentMergeForm

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.translated(get_language()).order_by('translations__name')

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
        segment_type_name = obj.segment_type.safe_translation_getter('name', obj.segment_type.slug)
        return format_html("<a href='{}'>{}</a>", url, segment_type_name)

    type_link.short_description = _('Segment type')

    def text_color(self, obj):
        return obj.text_color

    text_color.short_description = _("Text colour")


@admin.register(SegmentType)
class SegmentTypeAdmin(TranslatableLabelAdminMixin, TranslatableAdmin, admin.ModelAdmin, DynamicArrayMixin):
    model = SegmentType
    inlines = [SegmentInline]

    def get_prepopulated_fields(self, request, obj=None):
        return {'slug': ('name',)}

    def segments(self, obj):
        return obj.segments.count()

    segments.short_description = _('Number of segments')

    list_display = ['name', 'slug', 'segments', 'is_active', 'required', 'visibility']
    list_editable = ['is_active', 'required', 'visibility']

    fields = ['name', 'slug', 'inherit', 'visibility', 'required', 'needs_verification', 'is_active', 'user_editable',
              'enable_search', 'admin_user_filter', 'admin_activity_filter']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.translated(get_language()).order_by('translations__name')
