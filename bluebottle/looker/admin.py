from django.contrib import admin

from .models import LookerEmbed


class LookerEmmbedAdmin(admin.ModelAdmin):
    model = LookerEmbed
    list_display = ('title', 'type')


admin.site.register(LookerEmbed, LookerEmmbedAdmin)
