from django.contrib import admin
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

    raw_id_fields = ['author', 'parent', 'activity', 'contribution']
    fields = ['activity', 'created', 'author', 'parent', 'notify', 'video_url', 'message', 'pinned', 'contribution']

    list_display = ['created', 'activity', 'message']
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
