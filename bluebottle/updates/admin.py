from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django_admin_inline_paginator.admin import TabularInlinePaginated

from bluebottle.updates.models import Update, UpdateImage


class UpdateImageInline(admin.TabularInline):
    model = UpdateImage
    extra = 0


class ReplyInline(admin.TabularInline):
    model = Update
    fields = ['author', 'message']


@admin.register(Update)
class UpdateAdmin(admin.ModelAdmin):
    readonly_fields = ['created', 'notify']
    inlines = [UpdateImageInline]

    raw_id_fields = ['author', 'parent', 'activity']
    fields = ['activity', 'created', 'author', 'parent', 'notify', 'video_url', 'message', 'pinned']

    list_display = ['created', 'activity', 'message']
    list_filter = (('activity__polymorphic_ctype', admin.RelatedOnlyFieldListFilter),)


class UpdateInline(TabularInlinePaginated):
    model = Update
    per_page = 8
    extra = 0
    readonly_fields = ['created', 'author', 'parent', 'notify', 'has_images', 'has_video', 'message']
    fields = readonly_fields

    show_change_link = True

    def has_images(self, obj):
        return obj.images.length > 0
    has_images.short_description = _('has images')

    def has_video(self, obj):
        return bool(obj.video_url)
    has_video.short_description = _('has video')
