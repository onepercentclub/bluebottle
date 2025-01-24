from django.contrib import admin
from bluebottle.redirects.models import Redirect


class RedirectAdmin(admin.ModelAdmin):
    list_display = (
        'old_path',
        'new_path',
    )

    search_fields = ('old_path', 'new_path')


admin.site.register(Redirect, RedirectAdmin)
