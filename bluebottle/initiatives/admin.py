from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from polymorphic.admin import PolymorphicInlineSupportMixin

from bluebottle.activities.admin import ActivityAdminInline
from bluebottle.initiatives.models import Initiative
from bluebottle.notifications.admin import MessageAdminInline
from bluebottle.utils.admin import FSMAdmin


class InitiativeAdmin(PolymorphicInlineSupportMixin, FSMAdmin):
    fsm_field = 'status'

    raw_id_fields = ('owner', 'reviewer')
    list_display = ['title', 'created', 'status']
    list_filter = ['status']
    search_fields = ['title', 'pitch', 'story',
                     'owner__first_name', 'owner__last_name', 'owner__email']
    readonly_fields = ['status']

    def get_fieldsets(self, request, obj=None):
        return (
            (_('Basic'), {'fields': ('title', 'slug', 'owner', 'image', 'video_url')}),
            (_('Details'), {'fields': ('pitch', 'story', 'theme', 'categories', 'place')}),
            (_('Review'), {'fields': ('reviewer', 'status', 'status_transition')}),
        )

    inlines = [ActivityAdminInline, MessageAdminInline]


admin.site.register(Initiative, InitiativeAdmin)
