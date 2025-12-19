from django.contrib import admin

from .models import LookerEmbed


@admin.register(LookerEmbed)
class LookerEmbedAdmin(admin.ModelAdmin):
    model = LookerEmbed
    list_display = ('title', 'type')
