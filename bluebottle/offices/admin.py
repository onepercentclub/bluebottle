from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from bluebottle.geo.models import Location
from bluebottle.initiatives.models import Initiative
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
    list_display = ('name', 'region', 'offices', 'initiatives')
    model = OfficeSubRegion
    search_fields = ('name', 'description')
    raw_id_fields = ('region',)
    readonly_fields = ('offices', 'initiatives')
    list_filter = ('region',)

    inlines = [OfficeInline]

    def offices(self, obj):
        return format_html(
            u'<a href="{}?subregion__id__exact={}">{}</a>',
            reverse('admin:geo_location_changelist'),
            obj.id,
            len(Location.objects.filter(subregion=obj))
        )

    def initiatives(self, obj):
        return format_html(
            u'<a href="{}?location__subregion__id__exact={}">{}</a>',
            reverse('admin:initiatives_initiative_changelist'),
            obj.id,
            len(Initiative.objects.filter(location__subregion=obj))
        )

    fields = ('name', 'description', 'region', 'offices', 'initiatives')


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
    list_display = ('name', 'subregions_link', 'offices', 'initiatives')
    model = OfficeRegion
    search_fields = ('name', 'description')
    readonly_fields = ('offices', 'subregions_link', 'initiatives')
    inlines = [OfficeSubRegionInline]

    def subregions_link(self, obj):
        return format_html(
            u'<a href="{}?region__id__exact={}">{}</a>',
            reverse('admin:offices_officesubregion_changelist'),
            obj.id,
            len(OfficeSubRegion.objects.filter(region=obj))
        )
    subregions_link.short_description = _('office subregions')

    def offices(self, obj):
        return format_html(
            u'<a href="{}?subregion__region__id__exact={}">{}</a>',
            reverse('admin:geo_location_changelist'),
            obj.id,
            len(Location.objects.filter(subregion__region=obj))
        )

    def initiatives(self, obj):
        return format_html(
            u'<a href="{}?location__subregion__region__id__exact={}">{}</a>',
            reverse('admin:initiatives_initiative_changelist'),
            obj.id,
            len(Initiative.objects.filter(location__subregion__region=obj))
        )

    fields = ('name', 'description', 'subregions_link', 'offices', 'initiatives')
