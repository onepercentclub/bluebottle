from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from bluebottle.geo.models import Location
from bluebottle.offices.models import OfficeSubRegion, OfficeRegion


@admin.register(OfficeSubRegion)
class OfficeSubRegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'offices')
    model = OfficeSubRegion
    search_fields = ('name', 'description')
    raw_id_fields = ('region',)
    readonly_fields = ('offices',)
    list_filter = ('region',)

    def offices(self, obj):
        return format_html(
            u'<a href="{}?subregion__id__exact={}">{}</a>',
            reverse('admin:geo_location_changelist'),
            obj.id,
            len(Location.objects.filter(subregion=obj))
        )

    fields = ('name', 'description', 'region', 'offices')


@admin.register(OfficeRegion)
class OfficeRegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'subregions_link', 'offices')
    model = OfficeRegion
    search_fields = ('name', 'description')
    readonly_fields = ('offices', 'subregions_link')

    def subregions_link(self, obj):
        return format_html(
            u'<a href="{}?subregion__id__exact={}">{}</a>',
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

    fields = ('name', 'description', 'subregions_link', 'offices')
