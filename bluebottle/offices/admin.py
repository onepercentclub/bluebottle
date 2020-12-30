from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from bluebottle.geo.models import Location
from bluebottle.initiatives.models import Initiative
from bluebottle.offices.models import OfficeSubRegion, OfficeRegion


@admin.register(OfficeSubRegion)
class OfficeSubRegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'offices', 'initiatives')
    model = OfficeSubRegion
    search_fields = ('name', 'description')
    raw_id_fields = ('region',)
    readonly_fields = ('offices', 'initiatives')
    list_filter = ('region',)

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


@admin.register(OfficeRegion)
class OfficeRegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'subregions_link', 'offices', 'initiatives')
    model = OfficeRegion
    search_fields = ('name', 'description')
    readonly_fields = ('offices', 'subregions_link', 'initiatives')

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
