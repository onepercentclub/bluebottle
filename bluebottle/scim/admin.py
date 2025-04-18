from django.urls import re_path
from django.contrib import admin
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.urls import reverse

from bluebottle.bluebottle_dashboard.decorators import confirmation_form
from bluebottle.scim.forms import ResetTokenConfirmationForm
from bluebottle.scim.models import SCIMPlatformSettings, SCIMSegmentSetting
from bluebottle.utils.admin import BasePlatformSettingsAdmin, log_action


class SCIMSegmentSettingInline(admin.TabularInline):
    model = SCIMSegmentSetting
    fields = ('path', 'segment_type')
    extra = 0


@admin.register(SCIMPlatformSettings)
class SCIMPlatformSettingsAdmin(BasePlatformSettingsAdmin):
    readonly_fields = ('bearer_token', )
    inlines = [SCIMSegmentSettingInline]

    def get_urls(self):
        urls = super(SCIMPlatformSettingsAdmin, self).get_urls()
        custom_urls = [
            re_path(
                r'^(?P<pk>.+)/reset-token/$',
                self.admin_site.admin_view(self.reset_token),
                name='scim-platform-settings-reset-token',
            ),
        ]
        return custom_urls + urls

    @confirmation_form(
        ResetTokenConfirmationForm,
        SCIMPlatformSettings,
        'admin/reset_token_confirmation.html'
    )
    def reset_token(self, request, scim_settings):
        if not request.user.has_perm('scim.change_scimplatformsettings'):
            return HttpResponseForbidden('Missing permission: scim.change_scimplatformsettings')

        scim_settings.bearer_token = None
        scim_settings.save()

        log_action(scim_settings, request.user, 'Reset Token')
        url = reverse('admin:scim_scimplatformsettings_change', args=(scim_settings.pk,))
        return HttpResponseRedirect(url)
