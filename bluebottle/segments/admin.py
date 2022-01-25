from django import forms
from django.contrib import admin
from django.db import connection
from django.forms.models import ModelFormMetaclass
from django.utils.translation import gettext_lazy as _
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin

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

    extra = 0


@admin.register(SegmentType)
class SegmentAdmin(admin.ModelAdmin, DynamicArrayMixin):
    model = SegmentType
    inlines = [SegmentInline]

    def get_prepopulated_fields(self, request, obj=None):
        return {'slug': ('name',)}

    def segments(self, obj):
        return obj.segments.count()
    segments.short_description = _('Number of segments')

    list_display = ['name', 'slug', 'segments', 'is_active']
    list_editable = ['is_active']
