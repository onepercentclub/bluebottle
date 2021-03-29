from django.contrib import admin
from bluebottle.hooks.models import WebHook


@admin.register(WebHook)
class WebHookAdmin(admin.ModelAdmin):
    readonly_fields = ['secret_key']
