from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django_summernote.widgets import SummernoteWidget
from polymorphic.admin import PolymorphicInlineSupportMixin


from bluebottle.activities.admin import ActivityAdminInline
from bluebottle.initiatives.models import Initiative, InitiativePlatformSettings
from bluebottle.notifications.admin import MessageAdminInline
from bluebottle.utils.admin import FSMAdmin, BasePlatformSettingsAdmin
from bluebottle.utils.forms import FSMModelForm


class InitiativeAdminForm(FSMModelForm):

    class Meta:
        model = Initiative
        fields = '__all__'
        widgets = {
            'story': SummernoteWidget(attrs={'height': 400})
        }


@admin.register(Initiative)
class InitiativeAdmin(PolymorphicInlineSupportMixin, FSMAdmin):

    form = InitiativeAdminForm

    fsm_field = 'status'
    prepopulated_fields = {"slug": ("title",)}

    raw_id_fields = ('owner', 'reviewer')
    list_display = ['title', 'created', 'status']
    list_filter = ['status']
    search_fields = ['title', 'pitch', 'story',
                     'owner__first_name', 'owner__last_name', 'owner__email']
    readonly_fields = ['status']

    fieldsets = (
        (_('Basic'), {'fields': ('title', 'slug', 'owner', 'image', 'video_url')}),
        (_('Details'), {'fields': ('pitch', 'story', 'theme', 'categories', 'place')}),
        (_('Review'), {'fields': ('reviewer', 'status')}),
    )

    inlines = [ActivityAdminInline, MessageAdminInline]


@admin.register(InitiativePlatformSettings)
class InitiativePlatformSettingsAdmin(BasePlatformSettingsAdmin):
    pass
