from django import forms
from django.contrib import admin
from django.contrib.gis.db.models import PointField
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from parler.admin import TranslatableAdmin

from bluebottle.activities.models import Activity
from bluebottle.bluebottle_dashboard.admin import AdminMergeMixin
from bluebottle.geo.models import (
    Location, Country, Place,
    Geolocation, GeoFeature)
from bluebottle.geo.serializers import StaticMapsField
from bluebottle.geo.widgets import (
    CustomMapboxPointFieldWidget,
    GeolocationMapboxPointFieldWidget,
)
from bluebottle.utils.admin import TranslatableAdminOrderingMixin


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


@admin.register(GeoFeature)
class GeoFeatureAdmin(TranslatableAdmin):
    list_display = ('place_name', 'feature_type', 'mapbox_id', 'name')
    search_fields = ('mapbox_id', 'place_name', 'translations__name')
    readonly_fields = ('mapbox_id', 'feature_type', 'name', 'place_name')
    fields = ('mapbox_id', 'feature_type', 'place_name', 'name')


@admin.register(Country)
class CountryAdmin(TranslatableAdminOrderingMixin, TranslatableAdmin):
    list_display = ('name', 'alpha2_code', 'alpha3_code', 'numeric_code')
    search_fields = ('translations__name', 'alpha2_code', 'alpha3_code')
    fields = ('name', 'alpha2_code', 'alpha3_code', 'numeric_code')


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


@admin.register(Location)
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


class GeolocationGeoFeatureInline(admin.TabularInline):
    model = Geolocation.geofeatures.through
    extra = 0
    can_delete = False
    verbose_name = _('Geo feature')
    verbose_name_plural = _('Geo features')
    fields = ('feature_type', 'name', 'place_name')
    readonly_fields = ('feature_type', 'name', 'place_name')

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('geofeature').prefetch_related(
            'geofeature__translations'
        ).order_by(GeoFeature.type_order('geofeature__feature_type'), 'geofeature__id')

    @admin.display(description=_('Type'), ordering='geofeature__feature_type')
    def feature_type(self, obj):
        return obj.geofeature.feature_type or '-'

    @admin.display(description=_('Name'))
    def name(self, obj):
        return obj.geofeature.safe_translation_getter('name', any_language=True) or '-'

    @admin.display(description=_('Place name'))
    def place_name(self, obj):
        return obj.geofeature.safe_translation_getter('place_name', any_language=True) or '-'


@admin.register(Geolocation)
class GeolocationAdmin(admin.ModelAdmin):
    formfield_overrides = {
        PointField: {"widget": GeolocationMapboxPointFieldWidget},
    }
    list_display = ('geolocation_label', 'country')

    @admin.display(description=_('Geolocation'))
    def geolocation_label(self, obj):
        return str(obj)

    list_filter = ('country', )
    search_fields = ('mapbox_id', 'geofeatures__translations__name', 'geofeature__translations__name')
    inlines = (GeolocationGeoFeatureInline,)

    fieldsets = (
        (_('Location'), {'fields': ('position', 'place_name', 'mapbox_id', 'country')}),
    )

    readonly_fields = (
        'place_name', 'locality', 'street', 'street_number', 'postal_code',
        'province', 'formatted_address', 'map'
    )

    def map(self, obj):
        if not obj or not obj.position:
            return '-'

        url = StaticMapsField().to_representation(obj.position)
        return format_html(
            '<img src="{}" alt="{}" width="422" height="422" />',
            url,
            str(obj),
        )

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return True

    def get_fieldsets(self, request, obj=None):
        fieldsets = self.fieldsets
        if obj and obj.pk:
            fieldsets = (
                (_('Location'), {'fields': ('map', 'place_name', 'mapbox_id', 'country')}),
            )
        if request.user.is_superuser:
            fieldsets = fieldsets + (
                (_('Old info'), {
                    'fields': (
                        'locality', 'street', 'street_number', 'postal_code',
                        'province', 'formatted_address',
                    )
                }),
            )

        if obj and obj.pk:
            fieldsets = fieldsets + (
                (_('Related objects'), {'fields': ('related_objects_display',)}),
            )
        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if obj and obj.pk:
            fields = fields + ('related_objects_display',)
            return fields
        return fields

    @admin.display(description=_('Related objects'))
    def related_objects_display(self, obj):
        if not obj or not obj.pk:
            return '-'

        related = []
        for relation in obj._meta.related_objects:
            accessor_name = relation.get_accessor_name()
            if accessor_name in ['geofeatures', 'geofeature']:
                continue

            related_model = relation.related_model
            if related_model not in admin.site._registry:
                continue

            count = getattr(obj, accessor_name).count()
            if count == 0:
                continue

            meta = related_model._meta
            related.append({
                'count': count,
                'label': str(meta.verbose_name_plural),
                'url': reverse(
                    'admin:{}_{}_changelist'.format(meta.app_label, meta.model_name)
                ),
                'filter_param': '{}__id__exact'.format(relation.field.name),
            })

        if not related:
            return '-'

        return mark_safe(render_to_string(
            'admin/geo/geolocation_related_objects.html',
            {
                'related': related,
                'object_id': obj.pk,
            },
        ))
