from builtins import object
from django.contrib import admin
from django.urls import reverse
from django.utils import translation
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django_summernote.widgets import SummernoteWidget
from polymorphic.admin import PolymorphicInlineSupportMixin

from bluebottle.activities.admin import ActivityAdminInline
from bluebottle.geo.models import Location, Country
from bluebottle.initiatives.models import Initiative, InitiativePlatformSettings
from bluebottle.notifications.admin import MessageAdminInline, NotificationAdminMixin
from bluebottle.utils.admin import BasePlatformSettingsAdmin, export_as_csv_action
from bluebottle.fsm.admin import StateMachineAdmin, StateMachineFilter
from bluebottle.fsm.forms import StateMachineModelForm
from bluebottle.wallposts.admin import WallpostInline


class InitiativeAdminForm(StateMachineModelForm):

    class Meta(object):
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


class InitiativeCountryFilter(admin.SimpleListFilter):
    title = _("Country")
    parameter_name = 'country'

    def lookups(self, request, model_admin):
        language = translation.get_language()
        country_ids = Initiative.objects.\
            filter(place__isnull=False).distinct('place__country').\
            values_list('place__country__id', flat=True)
        countries = Country.objects.filter(id__in=country_ids).language(language).\
            order_by('translations__name')
        return [(c.id, c.name) for c in countries]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(place__country_id=self.value())
        return queryset


@admin.register(Initiative)
class InitiativeAdmin(PolymorphicInlineSupportMixin, NotificationAdminMixin, StateMachineAdmin):

    form = InitiativeAdminForm

    prepopulated_fields = {"slug": ("title",)}

    raw_id_fields = (
        'owner', 'reviewer',
        'promoter', 'activity_manager',
        'organization', 'organization_contact',
        'place'
    )

    date_hierarchy = 'created'
    list_display = ['__str__', 'created', 'owner', 'state_name']

    def get_list_display(self, request):
        fields = self.list_display
        if Location.objects.count():
            fields = fields + ['location_link']
        return fields

    list_filter = [InitiativeReviewerFilter, 'categories', 'theme', StateMachineFilter, ]

    def get_list_filter(self, request):
        filters = self.list_filter
        if Location.objects.count():
            if 'location' not in filters:
                filters += ['location']
            if InitiativePlatformSettings.objects.get().enable_office_regions \
                    and 'location__subregion' not in filters:
                filters += ['location__subregion', 'location__subregion__region']
        elif InitiativeCountryFilter not in filters:
            filters.append(InitiativeCountryFilter)

        return filters

    def location_link(self, obj):
        if not obj.location:
            return "-"
        url = reverse('admin:geo_location_change', args=(obj.location.id,))
        return format_html('<a href="{}">{}</a>', url, obj.location)
    location_link.short_description = _('office')

    search_fields = ['title', 'pitch', 'story',
                     'owner__first_name', 'owner__last_name', 'owner__email']

    readonly_fields = ['link', 'created', 'updated', 'valid']

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
        ('owner__full_name', 'Owner'),
        ('owner__email', 'Owner email'),
        ('activity_manager__full_name', 'Activity Manager'),
        ('activity_manager__email', 'Activity Manager email'),
        ('promotor__full_name', 'Promotor'),
        ('promotor__email', 'Promotor email'),
        ('reviewer__full_name', 'Reviewer'),
        ('reviewer__email', 'Reviewer email'),
    )

    actions = [export_as_csv_action(fields=export_to_csv_fields)]

    def get_fieldsets(self, request, obj=None):
        detail_fields = [
            'title', 'slug', 'owner',
            'theme', 'categories'
        ]

        if Location.objects.count():
            detail_fields.append('location')
        else:
            detail_fields.append('place')

        fieldsets = (
            (_('Details'), {'fields': detail_fields}),
            (_('Description'), {
                'fields': (
                    'pitch', 'story', 'image', 'video_url',
                )
            }),
            (_('Organization'), {
                'fields': (
                    'has_organization', 'organization',
                    'organization_contact'
                )
            }),
            (_('Status'), {'fields': (
                'valid',
                'reviewer', 'activity_manager',
                'promoter', 'status', 'states',
                'created', 'updated',
            )}),
        )
        if request.user.is_superuser:
            fieldsets += (
                (_('Super admin'), {'fields': (
                    'force_status',
                )}),
            )
        return fieldsets

    inlines = [ActivityAdminInline, MessageAdminInline, WallpostInline]

    def link(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>', obj.get_absolute_url, obj.title)
    link.short_description = _("Show on site")

    def valid(self, obj):
        errors = list(obj.errors)
        required = list(obj.required)
        if not errors and not required:
            return '-'

        errors += [
            _("{} is required").format(obj._meta.get_field(field).verbose_name.title())
            for field in required
        ]

        return format_html("<ul class='validation-error-list'>{}</ul>", format_html("".join([
            format_html(u"<li>{}</li>", value) for value in errors
        ])))

    valid.short_description = _('Steps to complete initiative')

    class Media(object):
        js = ('admin/js/inline-activities-add.js',)


@admin.register(InitiativePlatformSettings)
class InitiativePlatformSettingsAdmin(BasePlatformSettingsAdmin):
    pass
