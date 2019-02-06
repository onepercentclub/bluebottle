from django.contrib import admin
from bluebottle.token_auth.models import CheckedToken


class LoginTokenAdmin(admin.ModelAdmin):

    list_display = ('user', 'timestamp', 'short_token')

    def short_token(self, obj):
        return obj.token[:20] + '&hellip;'

    short_token.allow_tags = True


admin.site.register(CheckedToken, LoginTokenAdmin)
