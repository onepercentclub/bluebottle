from django.contrib import admin

from django_admin_inline_paginator.admin import TabularInlinePaginated
from bluebottle.updates.models import Update


@admin.register(Update)
class UpdateAdmin(admin.ModelAdmin):
    readonly_fields = ['created', 'notify']

    raw_id_fields = ['author', 'parent']
    fields = ['created', 'author', 'parent', 'notify', 'image', 'message']


class UpdateInline(TabularInlinePaginated):
    model = Update
    per_page = 8
    extra = 0
    readonly_fields = ['created', 'author', 'parent', 'notify', 'has_image', 'message']
    fields = ['created', 'author', 'parent', 'notify', 'has_image', 'message']

    show_change_link = True

    def has_image(self, obj):
        return obj.image is not None
