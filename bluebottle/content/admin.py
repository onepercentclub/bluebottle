from django.contrib import admin

from bluebottle.content.models import ContentBlock, ContentPage


class ContentBlockInline(admin.TabularInline):
    model = ContentBlock
    extra = 0
    fields = (
        'sort_order',
        'block_type',
        'title_text',
        'text',
        'align',
        'video_url',
        'button_label',
        'button_url',
        'spacer_size',
    )


@admin.register(ContentPage)
class ContentPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'language', 'status')
    list_filter = ('language', 'status')
    search_fields = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ContentBlockInline]
