from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from bluebottle.geo.models import Location

from .models import Region, SubRegion, Country


class LocationFilter(admin.SimpleListFilter):
    title = _('Location')
    parameter_name = 'location'

    def lookups(self, request, model_admin):
        locations = [obj.location for obj in model_admin.model.objects.order_by(
            'location__name').distinct('location__name').exclude(
            location__isnull=True).all()]
        return [(loc.id, loc.name) for loc in locations]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(location__id__exact=self.value())
        else:
            return queryset


class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'numeric_code')


admin.site.register(Region, RegionAdmin)


class SubRegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'numeric_code')
    list_filter = ('region',)


admin.site.register(SubRegion, SubRegionAdmin)


class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'alpha2_code', 'alpha3_code', 'numeric_code')
    list_filter = ('oda_recipient', 'subregion__region', 'subregion')
    search_fields = ('name', 'alpha2_code', 'alpha3_code')


admin.site.register(Country, CountryAdmin)


class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'position')
    model = Location


admin.site.register(Location, LocationAdmin)
