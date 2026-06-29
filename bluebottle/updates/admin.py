import os

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_admin_inline_paginator.admin import TabularInlinePaginated

from bluebottle.segments.filters import ActivitySegmentAdminMixin
from bluebottle.updates.models import Update, UpdateDocument, UpdateImage


class UpdateImageInline(admin.TabularInline):
    model = UpdateImage
    extra = 0
    raw_id_fields = ('image',)


class UpdateDocumentInline(admin.TabularInline):
    model = UpdateDocument
    extra = 0
    can_delete = True
    fields = ('document_link',)
    readonly_fields = ('document_link',)

    def has_add_permission(self, request, obj=None):
        return False

    def document_link(self, obj):
        if not obj.pk or not obj.document or not obj.document.file:
            return '-'
        url = reverse('update-document', args=(obj.pk,))
        filename = os.path.basename(obj.document.file.name)
        return format_html('<a href="{}" target="_blank">{}</a>', url, filename)

    document_link.short_description = _('Document')


@admin.register(UpdateDocument)
class UpdateDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'update', 'document_link')
    list_select_related = ('update', 'document')
    readonly_fields = ('update', 'document_link')
    fields = ('update', 'document_link')

    def has_add_permission(self, request):
        return False

    def document_link(self, obj):
        if not obj.document or not obj.document.file:
            return '-'
        url = reverse('update-document', args=(obj.pk,))
        filename = os.path.basename(obj.document.file.name)
        return format_html('<a href="{}" target="_blank">{}</a>', url, filename)

    document_link.short_description = _('Document')


class ReplyInline(admin.TabularInline):
    model = Update
    fields = ['author', 'message']


@admin.register(Update)
class UpdateAdmin(
    ActivitySegmentAdminMixin,
    admin.ModelAdmin
):
    readonly_fields = ['created', 'notify']
    inlines = [UpdateImageInline, UpdateDocumentInline]

    raw_id_fields = ['author', 'parent', 'activity', 'contribution']
    fields = ['activity', 'created', 'author', 'parent', 'notify', 'video_url', 'message', 'pinned',
              'contribution']

    list_display = ['created', 'activity']
    list_filter = (('activity__polymorphic_ctype', admin.RelatedOnlyFieldListFilter),)


class UpdateInline(TabularInlinePaginated):
    model = Update
    per_page = 8
    extra = 0
    readonly_fields = ['created', 'author', 'parent', 'message']
    fields = readonly_fields

    show_change_link = True

    def has_add_permission(self, request, obj):
        return False
