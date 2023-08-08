from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from django_admin_inline_paginator.admin import TabularInlinePaginated
from bluebottle.updates.models import Update


@admin.register(Update)
class UpdateAdmin(admin.ModelAdmin):
    readonly_fields = ['created', 'notify']

    raw_id_fields = ['author', 'parent']
    fields = ['created', 'author', 'parent', 'notify', 'image', 'video_url', 'message']


class UpdateInline(TabularInlinePaginated):
    model = Update
    per_page = 8
    extra = 0
    readonly_fields = ['created', 'author', 'parent', 'notify', 'has_image', 'has_video', 'message']
    fields = ['created', 'author', 'parent', 'notify', 'has_image', 'has_video', 'message']

    show_change_link = True

    def has_image(self, obj):
        return obj.image is not None
    has_image.short_description = _('has image')

    def has_video(self, obj):
        return bool(obj.video_url)
    has_video.short_description = _('has video')
