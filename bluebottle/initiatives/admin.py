from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django_summernote.widgets import SummernoteWidget
from polymorphic.admin import PolymorphicInlineSupportMixin

from bluebottle.activities.admin import ActivityAdminInline
from bluebottle.geo.models import Location
from bluebottle.initiatives.models import Initiative, InitiativePlatformSettings
from bluebottle.notifications.admin import MessageAdminInline
from bluebottle.utils.admin import FSMAdmin, BasePlatformSettingsAdmin, export_as_csv_action
from bluebottle.utils.forms import FSMModelForm


class InitiativeAdminForm(FSMModelForm):

    class Meta:
        model = Initiative
        fields = '__all__'
        widgets = {
            'story': SummernoteWidget(attrs={'height': 400})
        }


class InitiativeReviewerFilter(admin.SimpleListFilter):
    title = _('Reviewer')
    parameter_name = 'reviewer'

    def lookups(self, request, model_admin):
        reviewers = Initiative.objects.filter(reviewer__isnull=False). \
            distinct('reviewer__id', 'reviewer__first_name', 'reviewer__last_name'). \
            values_list('reviewer__id', 'reviewer__first_name', 'reviewer__last_name'). \
            order_by('reviewer__first_name', 'reviewer__last_name', 'reviewer__id')
        return [('me', _('My initiatives'))] + [(r[0], u"{} {}".format(r[1], r[2])) for r in reviewers]

    def queryset(self, request, queryset):
        if self.value() == 'me':
            return queryset.filter(
                reviewer=request.user
            )
        elif self.value():
            return queryset.filter(
                reviewer__id=self.value()
            )
        else:
            return queryset


@admin.register(Initiative)
class InitiativeAdmin(PolymorphicInlineSupportMixin, FSMAdmin):

    form = InitiativeAdminForm

    prepopulated_fields = {"slug": ("title",)}

    raw_id_fields = ('owner', 'reviewer', 'promoter', 'activity_manager',
                     'place', 'organization', 'organization_contact')

    date_hierarchy = 'created'
    list_display = ['__unicode__', 'created', 'owner', 'status']

    search_fields = ['title', 'pitch', 'story',
                     'owner__first_name', 'owner__last_name', 'owner__email']

    readonly_fields = ['status', 'link', 'created', 'updated']

    ordering = ('-created', )

    export_to_csv_fields = (
        ('title', 'Title'),
        ('status', 'Status'),
        ('created', 'Created'),
        ('pitch', 'Pitch'),
        ('theme', 'Theme'),
        ('image', 'Image'),
        ('video_url', 'Video'),
        ('place', 'Place'),
        ('location', 'Location'),
        ('organization', 'Organization'),
        ('owner', 'Owner'),
        ('activity_manager', 'Activity Manager'),
        ('promoter', 'Promoter'),
        ('reviewer', 'Reviewer'),
    )

    actions = [export_as_csv_action(fields=export_to_csv_fields)]

    def get_list_filter(self, instance):
        filters = [InitiativeReviewerFilter, 'categories', 'theme', 'status']

        if Location.objects.count():
            filters.append('location')
        else:
            filters.append('place')

        return filters

    def get_fieldsets(self, request, obj=None):
        details = ['pitch', 'story', 'theme', 'categories']

        if Location.objects.count():
            details.append('location')
        else:
            details.append('place')

        return (
            (_('Basic'), {'fields': (
                'title', 'link', 'slug', 'owner',
                'image', 'video_url',
                'created', 'updated')}),
            (_('Details'), {'fields': details}),
            (_('Organization'), {'fields': (
                'has_organization', 'organization', 'organization_contact')}),
            (_('Review'), {'fields': (
                'reviewer', 'activity_manager',
                'promoter', 'status', 'transitions')}),
        )

    inlines = [ActivityAdminInline, MessageAdminInline]

    def link(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>', obj.get_absolute_url, obj.title)
    link.short_description = _("Show on site")

    class Media:
        js = ('admin/js/inline-activities-add.js',)


@admin.register(InitiativePlatformSettings)
class InitiativePlatformSettingsAdmin(BasePlatformSettingsAdmin):
    pass
