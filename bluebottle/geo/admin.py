from django import forms
from django.contrib import admin
from django.contrib.gis.db.models import PointField
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from mapwidgets.widgets import MapboxPointFieldWidget
from parler.admin import TranslatableAdmin

from bluebottle.activities.models import Activity
from bluebottle.bluebottle_dashboard.admin import AdminMergeMixin
from bluebottle.geo.models import (
    Location, Country, Place,
    Geolocation, GeoFeature)
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


class LocationAdmin(AdminMergeMixin, admin.ModelAdmin, DynamicArrayMixin):
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

    subregion_link.short_description = _('Work location group')

    def region_link(self, obj):
        if not obj.subregion_id or not obj.subregion.region_id:
            return "-"
        url = reverse('admin:offices_officeregion_change', args=(obj.subregion.region_id,))
        return format_html('<a href="{}">{}</a>', url, obj.subregion.region)

    region_link.short_description = _('Work location region')

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


@admin.register(GeoFeature)
class GeoFeatureAdmin(TranslatableAdminOrderingMixin, TranslatableAdmin):
    list_display = ('name', 'place_type', 'code')
    list_filter = ('place_type',)
    search_fields = (
        'translations__name',
        'translations__place_name',
        'mapbox_id',
        'code',
    )
    fields = ('name', 'place_name', 'place_type', 'mapbox_id', 'code')


class GeoFeatureInline(admin.TabularInline):
    model = Geolocation.features.through
    extra = 0
    can_delete = False
    verbose_name = _('Geo-feature')
    verbose_name_plural = _('Geo-features')

    @admin.display(description=_('Level'))
    def place_type(self, obj):
        return obj.geofeature.place_type

    @admin.display(description=_('Mapbox id'))
    def mapbox_id(self, obj):
        return obj.geofeature.mapbox_id

    @admin.display(description=_('Code'))
    def code(self, obj):
        return obj.geofeature.code

    @admin.display(description=_('Name'))
    def name(self, obj):
        return obj.geofeature.name

    @admin.display(description=_('Title'))
    def title(self, obj):
        return obj.geofeature.place_name

    readonly_fields = ('place_type', 'code', 'name', 'title')
    fields = readonly_fields

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class GeolocationAdminForm(forms.ModelForm):
    class Meta(object):
        model = Geolocation
        fields = '__all__'
        widgets = {
            'mapbox_id': forms.HiddenInput()
        }



@admin.register(Geolocation)
class GeolocationAdmin(admin.ModelAdmin):
    class Media(object):
        js = ('geo/js/geolocation_admin_mapbox.js',)

    form = GeolocationAdminForm

    formfield_overrides = {
        PointField: {"widget": CustomMapboxPointFieldWidget},
    }

    list_display = ('geolocation_label', 'street', 'locality', 'country')

    @admin.display(description=_('Geolocation'))
    def geolocation_label(self, obj):
        return str(obj)

    list_filter = ('country', )
    readonly_fields = ('place_name',)
    search_fields = ('locality', 'street', 'formatted_address', 'mapbox_id')

    inlines = [GeoFeatureInline]

    def place_name(self, obj):
        return str(obj)

    fieldsets = (
        (_('Map'), {'fields': ('position', 'mapbox_id', 'place_name')}),
        (_('Info'), {
            'fields': (
                'locality', 'street', 'street_number', 'postal_code',
                'province', 'country', 'formatted_address'
            )
        })
    )
