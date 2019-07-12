from django.contrib import admin
from django.utils.html import format_html
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

    prepopulated_fields = {"slug": ("title",)}

    raw_id_fields = ('owner', 'reviewer', 'promoter', 'activity_manager',
                     'place', 'organization', 'organization_contact')
    list_display = ['title_display', 'created', 'status']
    list_filter = ['status']
    search_fields = ['title', 'pitch', 'story',
                     'owner__first_name', 'owner__last_name', 'owner__email']
    readonly_fields = ['status', 'link']

    fieldsets = (
        (_('Basic'), {'fields': ('title', 'link', 'slug', 'owner', 'image', 'video_url')}),
        (_('Details'), {'fields': ('pitch', 'story', 'theme', 'categories', 'location', 'place')}),
        (_('Organization'), {'fields': ('organization', 'organization_contact')}),
        (_('Review'), {'fields': ('reviewer', 'activity_manager', 'promoter', 'status', 'status_transition')}),
    )

    def title_display(self, obj):
        return obj.title or _('- empty -')
    title_display.short_description = _('Title')

    inlines = [ActivityAdminInline, MessageAdminInline]

    def link(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>', obj.full_url, obj.title)
    link.short_description = _("Show on site")

    class Media:
        js = ('admin/js/inline-activities-add.js',)


@admin.register(InitiativePlatformSettings)
class InitiativePlatformSettingsAdmin(BasePlatformSettingsAdmin):
    pass
