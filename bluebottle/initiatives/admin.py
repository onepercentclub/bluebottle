from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from polymorphic.admin import PolymorphicInlineSupportMixin


from bluebottle.activities.admin import ActivityAdminInline
from bluebottle.initiatives.models import Initiative, InitiativePlatformSettings
from bluebottle.notifications.admin import MessageAdminInline
from bluebottle.utils.admin import FSMAdmin, BasePlatformSettingsAdmin


class InitiativeAdmin(PolymorphicInlineSupportMixin, FSMAdmin):
    fsm_field = 'status'

    raw_id_fields = ('owner', 'reviewer')
    list_display = ['title', 'created', 'status']
    list_filter = ['status']
    search_fields = ['title', 'pitch', 'story',
                     'owner__first_name', 'owner__last_name', 'owner__email']
    readonly_fields = ['status', 'link']

    fieldsets = (
        (_('Basic'), {'fields': ('title', 'link', 'slug', 'owner', 'image', 'video_url')}),
        (_('Details'), {'fields': ('pitch', 'story', 'theme', 'categories', 'place')}),
        (_('Review'), {'fields': ('reviewer', 'status')}),
    )

    inlines = [ActivityAdminInline, MessageAdminInline]

    def link(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>', obj.full_url, obj.title)
    link.short_description = _("Show on site")


class InitiativePlatformSettingsAdmin(BasePlatformSettingsAdmin):
    pass


admin.site.register(Initiative, InitiativeAdmin)
admin.site.register(InitiativePlatformSettings, InitiativePlatformSettingsAdmin)
