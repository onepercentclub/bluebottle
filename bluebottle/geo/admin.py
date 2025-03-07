from django import forms
from django.contrib import admin
from django.contrib.gis.db.models import PointField
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from mapwidgets.widgets import MapboxPointFieldWidget

from parler.admin import TranslatableAdmin

from bluebottle.activities.models import Activity
from bluebottle.bluebottle_dashboard.admin import AdminMergeMixin
from bluebottle.geo.models import (
    Location, Country, Place,
    Geolocation)
from bluebottle.utils.admin import TranslatableAdminOrderingMixin


class CustomMapboxPointFieldWidget(MapboxPointFieldWidget):

    @property
    def media(self):
        return self._media(
            extra_js=[
                "https://api.mapbox.com/mapbox-gl-js/v3.3.0/mapbox-gl.js",
                "/static/assets/admin/js/mapbox-sdk.min.js",
                "https://api.mapbox.com/mapbox-gl-js/plugins/mapbox-gl-geocoder/v4.7.2/mapbox-gl-geocoder.min.js",
            ],
            extra_css=[
                "https://api.mapbox.com/mapbox-gl-js/v3.3.0/mapbox-gl.css",
                "https://api.mapbox.com/mapbox-gl-js/plugins/mapbox-gl-geocoder/v4.7.2/mapbox-gl-geocoder.css",
            ],
        )


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


class CountryAdmin(TranslatableAdminOrderingMixin, TranslatableAdmin):
    list_display = ('name', 'alpha2_code', 'alpha3_code', 'numeric_code')
    search_fields = ('translations__name', 'alpha2_code', 'alpha3_code')
    fields = ('name', 'alpha2_code', 'alpha3_code', 'numeric_code')


admin.site.register(Country, CountryAdmin)


class LocationMergeForm(forms.Form):
    to = forms.ModelChoiceField(
        label=_("Merge with"),
        help_text=_("Choose location to merge with"),
        queryset=Location.objects.all(),
    )

    title = _("Merge")

    def __init__(self, obj, *args, **kwargs):
        super(LocationMergeForm, self).__init__(*args, **kwargs)

        self.fields["to"].queryset = self.fields["to"].queryset.exclude(pk=obj.pk)


class LocationAdmin(AdminMergeMixin, admin.ModelAdmin):
    formfield_overrides = {
        PointField: {"widget": CustomMapboxPointFieldWidget},
    }

    def get_queryset(self, request):
        queryset = super(LocationAdmin, self).get_queryset(request)
        if request.user.subregion_manager.count():
            queryset = queryset.filter(subregion__in=request.user.subregion_manager.all())
        return queryset

    def lookup_allowed(self, key, value):
        if key in ('subregion__region__id__exact',):
            return True
        return super(LocationAdmin, self).lookup_allowed(key, value)

    list_display = ('name', 'slug', 'subregion_link', 'region_link', 'activities', 'country')
    model = Location
    search_fields = ('name', 'description', 'city')
    verbose_name_plural = 'test'

    list_filter = ('subregion', 'subregion__region')

    def activities(self, obj):
        return format_html(
            u'<a href="{}?office_location__id__exact={}">{}</a>',
            reverse('admin:activities_activity_changelist'),
            obj.id,
            len(Activity.objects.filter(office_location=obj))
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
        (
            _("Info"),
            {
                "fields": (
                    "name",
                    "slug",
                    "subregion",
                    "description",
                    "city",
                    "country",
                    "image",
                )
            },
        ),
        (_("Map"), {"fields": ("position",)}),
        (_("SSO"), {"fields": ("alternate_names",)}),
    )

    merge_form = LocationMergeForm


@admin.register(Place)
class PlaceInline(admin.ModelAdmin):
    formfield_overrides = {
        PointField: {"widget": CustomMapboxPointFieldWidget},
    }
    model = Place
    fields = [
        'street',
        'locality',
        'postal_code',
        'country',
        'formatted_address',
        'position',
        'mapbox_id'
    ]


admin.site.register(Location, LocationAdmin)


@admin.register(Geolocation)
class GeolocationAdmin(admin.ModelAdmin):
    formfield_overrides = {
        PointField: {"widget": CustomMapboxPointFieldWidget},
    }
    list_display = ('__str__', 'street', 'locality', 'country')

    list_filter = ('country', )
    search_fields = ('locality', 'street', 'formatted_address', 'mapbox_id')

    fieldsets = (
        (_('Map'), {'fields': ('position', )}),
        (_('Info'), {
            'fields': (
                'locality', 'street', 'street_number', 'postal_code',
                'province', 'country', 'formatted_address', 'mapbox_id'
            )
        })
    )

    def get_fieldsets(self, request, obj):
        if obj and obj.position:
            return self.fieldsets
        return (
            (_('Map'), {'fields': ('position', )}),
        )
