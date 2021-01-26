from django.contrib import admin
from django.contrib.contenttypes.admin import GenericStackedInline
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from parler.admin import TranslatableAdmin

from bluebottle.geo.models import (
    Location, Country, Place,
    InitiativePlace, Geolocation)
from bluebottle.initiatives.models import Initiative


class LocationFilter(admin.SimpleListFilter):
    title = _('Location')
    parameter_name = 'location'

    def lookups(self, request, model_admin):
        locations = [obj.location for obj in model_admin.model.objects.order_by(
            'location__name').distinct('location__name').exclude(
            location__isnull=True).all()]
        lookups = [(loc.id, loc.name) for loc in locations]

        try:
            lookups.insert(
                0, (request.user.location.id, _('My location ({})').format(request.user.location))
            )
        except AttributeError:
            pass

        return lookups

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(location__id__exact=self.value())
        else:
            return queryset


class CountryAdmin(TranslatableAdmin):
    list_display = ('name', 'alpha2_code', 'alpha3_code', 'numeric_code')
    search_fields = ('name', 'alpha2_code', 'alpha3_code')
    fields = ('name', 'alpha2_code', 'alpha3_code', 'numeric_code')


admin.site.register(Country, CountryAdmin)


class LocationAdmin(admin.ModelAdmin):

    def lookup_allowed(self, key, value):
        if key in ('subregion__region__id__exact',):
            return True
        return super(LocationAdmin, self).lookup_allowed(key, value)

    list_display = ('name', 'slug', 'subregion_link', 'region_link', 'initiatives')
    model = Location
    search_fields = ('name', 'description', 'city')
    verbose_name_plural = 'test'

    list_filter = ('subregion', 'subregion__region')

    def initiatives(self, obj):
        return format_html(
            u'<a href="{}?location__id__exact={}">{}</a>',
            reverse('admin:initiatives_initiative_changelist'),
            obj.id,
            len(Initiative.objects.filter(location=obj))
        )

    def subregion_link(self, obj):
        if not obj.subregion_id:
            return "-"
        url = reverse('admin:offices_officesubregion_change', args=(obj.subregion_id,))
        return format_html('<a href="{}">{}</a>', url, obj.subregion)
    subregion_link.short_description = _('Office group')

    def region_link(self, obj):
        if not obj.subregion_id or not obj.subregion.region_id:
            return "-"
        url = reverse('admin:offices_officeregion_change', args=(obj.subregion.region_id,))
        return format_html('<a href="{}">{}</a>', url, obj.subregion.region)
    region_link.short_description = _('Office region')

    fieldsets = (
        (_('Info'), {'fields': ('name', 'subregion', 'description', 'city', 'country', 'image')}),
        (_('Map'), {'fields': ('position', )})
    )


class PlaceInline(GenericStackedInline):
    model = Place
    max_num = 1


admin.site.register(Location, LocationAdmin)


@admin.register(InitiativePlace)
class InitiativePlaceAdmin(admin.ModelAdmin):

    fieldsets = (
        (_('Info'), {'fields': ('street', 'street_number', 'postal_code',
                                'province', 'country', 'formatted_address')}),
        (_('Map'), {'fields': ('position', )})
    )


@admin.register(Geolocation)
class GeolocationAdmin(admin.ModelAdmin):

    list_display = ('__str__', 'street', 'locality', 'country')

    list_filter = ('country', )
    search_fields = ('locality', 'street', 'formatted_address')

    fieldsets = (
        (_('Map'), {'fields': ('position', )}),
        (_('Info'), {
            'fields': (
                'locality', 'street', 'street_number', 'postal_code',
                'province', 'country', 'formatted_address'
            )
        })
    )
