from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from bluebottle.analytics.models import AnalyticsPlatformSettings
from bluebottle.utils.admin import BasePlatformSettingsAdmin


@admin.register(AnalyticsPlatformSettings)
class AnalyticsPlatformSettingsAdmin(BasePlatformSettingsAdmin):
    fieldsets = (
        (
            _('General'),
            {
                'fields': [
                    'platform_type', 'plausible_embed_link', 'terminated',

                ]
            }
        ),
        (
            _('Targets'),
            {
                'fields': [
                    'user_base', 'engagement_target', 'acts_of_impact_target',
                    'hours_spent_target', 'amount_raised_target'
                ]
            }
        ),

    )
