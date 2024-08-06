from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from bluebottle.activities.models import Activity
from bluebottle.geo.models import Location
from bluebottle.offices.models import OfficeSubRegion, OfficeRegion


class OfficeInline(admin.TabularInline):
    model = Location
    fields = ['link', 'name']
    readonly_fields = ['link']
    extra = 0

    def link(self, obj):
        url = reverse('admin:geo_location_change', args=(obj.id,))
        return format_html('<a href="{}">{}</a>', url, obj)


@admin.register(OfficeSubRegion)
class OfficeSubRegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'offices', 'activities')
    model = OfficeSubRegion
    search_fields = ('name', 'description')
    raw_id_fields = ('region',)
    readonly_fields = ('offices', 'activities')
    list_filter = ('region',)

    inlines = [OfficeInline]

    def offices(self, obj):
        return format_html(
            u'<a href="{}?subregion__id__exact={}">{}</a>',
            reverse('admin:geo_location_changelist'),
            obj.id,
            len(Location.objects.filter(subregion=obj))
        )

    def activities(self, obj):
        return format_html(
            u'<a href="{}?office_location__subregion__id__exact={}">{}</a>',
            reverse('admin:activities_activity_changelist'),
            obj.id,
            len(Activity.objects.filter(office_location__subregion=obj))
        )

    fields = ('name', 'description', 'region', 'offices', 'activities')


class OfficeSubRegionInline(admin.TabularInline):
    model = OfficeSubRegion
    fields = ['link', 'name']
    readonly_fields = ['link']
    extra = 0

    def link(self, obj):
        url = reverse('admin:offices_officesubregion_change', args=(obj.id,))
        return format_html('<a href="{}">{}</a>', url, obj)


@admin.register(OfficeRegion)
class OfficeRegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'subregions_link', 'offices', 'activities')
    model = OfficeRegion
    search_fields = ('name', 'description')
    readonly_fields = ('offices', 'subregions_link', 'activities')
    inlines = [OfficeSubRegionInline]

    def subregions_link(self, obj):
        return format_html(
            u'<a href="{}?region__id__exact={}">{}</a>',
            reverse('admin:offices_officesubregion_changelist'),
            obj.id,
            len(OfficeSubRegion.objects.filter(region=obj))
        )
    subregions_link.short_description = _('office groups')

    def offices(self, obj):
        return format_html(
            u'<a href="{}?subregion__region__id__exact={}">{}</a>',
            reverse('admin:geo_location_changelist'),
            obj.id,
            len(Location.objects.filter(subregion__region=obj))
        )

    def activities(self, obj):
        return format_html(
            u'<a href="{}?office_location__subregion__region__id__exact={}">{}</a>',
            reverse('admin:activities_activity_changelist'),
            obj.id,
            len(Activity.objects.filter(office_location__subregion__region=obj))
        )

    fields = ('name', 'description', 'subregions_link', 'offices', 'activities')


class OfficeManagerAdminMixin:

    office_subregion_path = 'office_location__subregion'

    def get_queryset(self, request):
        queryset = super(OfficeManagerAdminMixin, self).get_queryset(request)
        if request.user.region_manager:
            region_manager_filter = {self.office_subregion_path: request.user.region_manager}
            queryset = queryset.filter(**region_manager_filter)
        return queryset
