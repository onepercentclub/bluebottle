from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from bluebottle.initiatives.models import Initiative
from bluebottle.notifications.admin import MessageAdminInline
from bluebottle.utils.admin import ReviewAdmin


class InitiativeAdmin(ReviewAdmin):
    raw_id_fields = ('owner', 'reviewer',)

    list_display = ['title']
    readonly_fields = ['review_status']

    def get_fieldsets(self, request, obj=None):
        return (
            (_('Basic'), {'fields': ('title', 'slug', 'owner', 'image', 'video_url')}),
            (_('Details'), {'fields': ('pitch', 'story', 'theme', 'categories')}),
            (_('Review'), {'fields': ('reviewer', 'review_status', 'review_status_transition')}),
        )

    inlines = [MessageAdminInline, ]


admin.site.register(Initiative, InitiativeAdmin)
