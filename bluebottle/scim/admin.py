from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.urls import reverse

from bluebottle.scim.models import SCIMPlatformSettings
from bluebottle.utils.admin import BasePlatformSettingsAdmin


class SCIMPlatformSettingsAdmin(BasePlatformSettingsAdmin):
    readonly_fields = ('bearer_token', )

    def get_urls(self):
        urls = super(SCIMPlatformSettingsAdmin, self).get_urls()
        custom_urls = [
            url(
                r'^(?P<pk>.+)/reset-token/$',
                self.admin_site.admin_view(self.reset_token),
                name='scim-platform-settings-reset-token',
            ),
        ]
        return custom_urls + urls

    def reset_token(self, request, pk):
        if request.method == 'POST':
            if (
                request.user.is_active
                and request.user.has_permission('scim.change_scimplatformsettings')
            ):
                scim_settings = SCIMPlatformSettings.objects.get(pk=pk)

                scim_settings.bearer_token = None
                scim_settings.save()
            else:
                return HttpResponseForbidden()

        url = reverse('admin:scim_scimplatformsettings_change', args=(pk,))
        return HttpResponseRedirect(url)


admin.site.register(SCIMPlatformSettings, SCIMPlatformSettingsAdmin)
