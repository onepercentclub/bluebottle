from builtins import object

from django.conf import settings
from django.contrib.gis.geos import Point
from django.utils.translation import get_language
from rest_framework import serializers
from rest_framework_json_api.serializers import ModelSerializer
from staticmaps_signature import StaticMapURLSigner
from timezonefinder import TimezoneFinder

from bluebottle.bluebottle_drf2.serializers import ImageSerializer
from bluebottle.geo.mapbox import FEATURE_TYPE_HIERARCHY
from bluebottle.geo.models import Country, Location, Place, Geolocation

staticmap_url_signer = StaticMapURLSigner(
    public_key=settings.STATIC_MAPS_API_KEY, private_key=settings.STATIC_MAPS_API_SECRET
)

tf = TimezoneFinder()


# ---------------------------------------------------------------------------
# Location display formatting (geofeatures + card_location_display)
# ---------------------------------------------------------------------------

CARD_LOCATION_MODES = frozenset({
    'neighbourhood',
    'neighbourhood_city',
    'city',
    'city_region',
    'city_country',
})

CARD_LOCATION_COMMON_LEVEL_CHECKS = {
    'neighbourhood': (
        ('neighborhood',),
        ('locality',),
        ('city',),
        ('region',),
        ('country',),
    ),
    'neighbourhood_city': (
        ('neighborhood', 'city'),
        ('locality', 'city'),
        ('city',),
        ('region',),
        ('country',),
    ),
    'city': (
        ('city',),
        ('region',),
        ('country',),
    ),
    'city_region': (
        ('city', 'region'),
        ('region',),
        ('country',),
    ),
    'city_country': (
        ('city', 'country'),
        ('region', 'country'),
        ('country',),
    ),
}


def _attr(entry, key, default=None):
    if entry is None:
        return default
    if isinstance(entry, dict):
        return entry.get(key, default)
    return getattr(entry, key, default)


def _entries_for_language(entries, language):
    if not isinstance(language, str):
        language = 'en'

    matched = [entry for entry in entries if _attr(entry, 'language') == language]
    if matched:
        return matched

    prefix = language.split('-')[0]
    return [
        entry for entry in entries
        if _attr(entry, 'language', '').startswith(prefix)
    ]


def get_translated_geofeature_list(geofeature, country=None, is_primary=False):
    from bluebottle.utils.models import Language

    data = []
    current_language = geofeature._current_language
    country_language = country._current_language if country else None

    for lang in Language.objects.all():
        if not geofeature.has_translation(lang.full_code):
            continue

        geofeature.set_current_language(lang.full_code)
        name = geofeature.name
        place_name = geofeature.place_name
        if not name and not place_name:
            continue

        entry = {
            'id': geofeature.pk,
            'name': name or '',
            'place_name': place_name or '',
            'language': lang.full_code,
            'feature_type': geofeature.feature_type or '',
            'is_primary': is_primary,
        }
        if country and country.has_translation(lang.full_code):
            country.set_current_language(lang.full_code)
            entry['country'] = country.name
            entry['country_code'] = country.alpha2_code
        data.append(entry)

    geofeature._current_language = current_language
    if country and country_language is not None:
        country._current_language = country_language
    return data


def geofeatures_for_geolocation(geolocation):
    geofeatures = []
    primary_id = geolocation.geofeature_id
    country = geolocation.country
    for geofeature in geolocation.geofeatures.all():
        geofeatures.extend(get_translated_geofeature_list(
            geofeature,
            country=country,
            is_primary=geofeature.pk == primary_id,
        ))
    return geofeatures


def locality_from_geolocation(geolocation):
    if not geolocation:
        return None

    primary = geolocation.geofeature
    if primary and primary.feature_type in ('place', 'locality'):
        return primary.name

    for geofeature in geolocation.geofeatures.all():
        if geofeature.feature_type in ('place', 'locality'):
            return geofeature.name
    return None


def formatted_address_from_geolocation(geolocation):
    if not geolocation:
        return None

    for geofeature in geolocation.geofeatures.all():
        if geofeature.feature_type == 'address':
            return geofeature.place_name or geofeature.name

    primary = geolocation.geofeature
    if primary:
        return primary.place_name or primary.name
    return None


def _feature_name(geofeatures, feature_type):
    feature = next(
        (item for item in geofeatures if _attr(item, 'feature_type') == feature_type),
        None,
    )
    return _attr(feature, 'name') if feature else None


def _card_location_parts(activity, language_geofeatures, language):
    place = _feature_name(language_geofeatures, 'place')
    locality = _feature_name(language_geofeatures, 'locality')
    city = place or locality

    country_feature = next(
        (
            item for item in language_geofeatures
            if _attr(item, 'feature_type') == 'country'
        ),
        None,
    )
    country = (
        _attr(country_feature, 'name')
        or _attr(country_feature, 'place_name')
        or next(
            (
                _attr(item, 'country')
                for item in language_geofeatures
                if _attr(item, 'country')
            ),
            None,
        )
    )
    if not country:
        countries = _entries_for_language(getattr(activity, 'country', None) or [], language)
        if countries:
            country = _attr(countries[0], 'name')

    country_code = (
        _attr(country_feature, 'country_code')
        or next(
            (
                _attr(item, 'country_code')
                for item in language_geofeatures
                if _attr(item, 'country_code')
            ),
            None,
        )
    )

    return {
        'neighborhood': _feature_name(language_geofeatures, 'neighborhood'),
        'locality': locality,
        'city': city,
        'region': _feature_name(language_geofeatures, 'region'),
        'country': country,
        'country_code': country_code,
    }


def format_card_location_from_parts(mode, parts):
    if mode not in CARD_LOCATION_MODES:
        return None

    country = parts.get('country')
    country_code = parts.get('country_code')
    country_label = country or country_code
    country_abbrev = country_code or country

    if mode == 'neighbourhood':
        return (
            parts.get('neighborhood')
            or parts.get('city')
            or parts.get('region')
            or country
            or country_code
        )

    if mode == 'neighbourhood_city':
        neighborhood = parts.get('neighborhood')
        locality = parts.get('locality')
        city = parts.get('city')
        if neighborhood and city:
            return '{}, {}'.format(neighborhood, city)
        if locality and city and locality != city:
            return '{}, {}'.format(locality, city)
        if city:
            return city
        if locality:
            return locality
        if neighborhood:
            return neighborhood
        return parts.get('region') or country_label or country_code

    if mode == 'city':
        return parts.get('city') or parts.get('region') or country or country_code

    if mode == 'city_region':
        city = parts.get('city')
        region = parts.get('region')
        if city and region:
            return '{}, {}'.format(city, region)
        if region:
            return region
        return country_label

    if mode == 'city_country':
        city = parts.get('city')
        region = parts.get('region')
        if city and country_abbrev:
            return '{}, {}'.format(city, country_abbrev)
        if region and country_abbrev:
            return '{}, {}'.format(region, country_abbrev)
        return country_label

    return None


def format_card_location_from_values(mode, **kwargs):
    return format_card_location_from_parts(mode, kwargs)


def card_location_parts_from_geofeatures(activity, geofeatures, language):
    if not geofeatures:
        return None
    language_geofeatures = _entries_for_language(geofeatures, language)
    if not language_geofeatures:
        return None
    return _card_location_parts(activity, language_geofeatures, language)


def format_card_location(activity, card_location_display, language, geofeatures=None):
    if card_location_display not in CARD_LOCATION_MODES:
        return None

    if geofeatures is None:
        geofeatures = getattr(activity, 'geofeature', None)
    if not geofeatures:
        return None

    language_geofeatures = _entries_for_language(geofeatures, language)
    if not language_geofeatures:
        return None

    return format_card_location_from_parts(
        card_location_display,
        _card_location_parts(activity, language_geofeatures, language),
    )


def card_location_for_geolocation(geolocation, language=None, activity=None):
    from bluebottle.initiatives.models import InitiativePlatformSettings

    language = (language or get_language() or 'en').split(',')[0]
    activity = activity or type('Activity', (), {'country': []})()
    return format_card_location(
        activity,
        InitiativePlatformSettings.load().card_location_display,
        language,
        geofeatures=geofeatures_for_geolocation(geolocation),
    )


def _common_parts_for_keys(all_parts, keys):
    if not all_parts:
        return None

    merged = {
        'neighborhood': None,
        'locality': None,
        'city': None,
        'region': None,
        'country': None,
        'country_code': None,
    }

    for key in keys:
        if key == 'country':
            country_keys = [
                part.get('country_code') or part.get('country')
                for part in all_parts
            ]
            if any(not value for value in country_keys) or len(set(country_keys)) != 1:
                return None
            merged['country'] = all_parts[0].get('country')
            merged['country_code'] = all_parts[0].get('country_code')
        else:
            values = [part.get(key) for part in all_parts if part]
            if any(not value for value in values) or len(set(values)) != 1:
                return None
            merged[key] = values[0]

    return merged


def format_common_card_location(activity, card_location_display, language, location_parts):
    if card_location_display not in CARD_LOCATION_MODES or not location_parts:
        return None

    for keys in CARD_LOCATION_COMMON_LEVEL_CHECKS.get(card_location_display, ()):
        common_parts = _common_parts_for_keys(location_parts, keys)
        if not common_parts:
            continue
        formatted = format_card_location_from_parts(card_location_display, common_parts)
        if formatted:
            return formatted
    return None


def _geofeature_names_for_geolocation(geolocation, language):
    names = {}
    for geofeature in geolocation.geofeatures.all():
        geofeature.set_current_language(language)
        feature_type = geofeature.feature_type
        name = geofeature.name or geofeature.place_name
        if feature_type and name:
            names[feature_type] = name
    return names


def _geofeature_names_from_entries(geofeatures, language):
    names = {}
    for entry in _entries_for_language(geofeatures, language):
        feature_type = _attr(entry, 'feature_type')
        name = _attr(entry, 'name') or _attr(entry, 'place_name')
        if feature_type and name:
            names[feature_type] = name
    return names


def _shared_geofeature_names(name_maps):
    if len(name_maps) < 2:
        return {}

    shared = {}
    for feature_type in FEATURE_TYPE_HIERARCHY:
        values = [name_map.get(feature_type) for name_map in name_maps]
        if any(not value for value in values) or len(set(values)) != 1:
            continue
        shared[feature_type] = values[0]
    return shared


def _format_shared_address(shared):
    if not shared:
        return None
    if shared.get('address'):
        return shared['address']

    parts = []
    if shared.get('street'):
        parts.append(shared['street'])

    city = shared.get('place') or shared.get('locality')
    city_line = ' '.join(part for part in (shared.get('postcode'), city) if part)
    if city_line:
        parts.append(city_line)
    elif city:
        parts.append(city)

    if shared.get('region') and not city:
        parts.append(shared['region'])
    if shared.get('country'):
        parts.append(shared['country'])

    return ', '.join(parts) if parts else None


def common_formatted_address_for_geolocations(geolocations, language=None):
    language = (language or get_language() or 'en').split(',')[0]
    return _format_shared_address(_shared_geofeature_names([
        _geofeature_names_for_geolocation(geolocation, language)
        for geolocation in geolocations
    ]))


def common_formatted_address_from_geofeatures(geofeature_groups, language=None):
    language = (language or get_language() or 'en').split(',')[0]
    return _format_shared_address(_shared_geofeature_names([
        _geofeature_names_from_entries(geofeatures, language)
        for geofeatures in geofeature_groups
    ]))


def format_multi_location_label(activity, card_location_display, language, geolocations):
    language = (language or get_language() or 'en').split(',')[0]
    street_address = common_formatted_address_for_geolocations(geolocations, language)

    location_parts = [
        card_location_parts_from_geofeatures(
            activity,
            geofeatures_for_geolocation(geolocation),
            language,
        )
        for geolocation in geolocations
    ]
    card_address = format_common_card_location(
        activity, card_location_display, language, location_parts
    )

    name_maps = [
        _geofeature_names_for_geolocation(geolocation, language)
        for geolocation in geolocations
    ]
    shared = _shared_geofeature_names(name_maps)
    if street_address and ('address' in shared or 'street' in shared):
        return street_address

    return card_address or street_address


class PointSerializer(serializers.CharField):

    def to_representation(self, instance):
        return {
            'longitude': instance.coords[0],
            'latitude': instance.coords[1]
        }

    def to_internal_value(self, data):
        if not data:
            return None
        try:
            point = Point(float(data['longitude']), float(data['latitude']))
        except ValueError as e:
            raise serializers.ValidationError("Invalid point. {}".format(e))
        return point


class StaticMapsField(serializers.ReadOnlyField):
    url = (
        "https://maps.googleapis.com/maps/api/staticmap"
        "?center={latitude},{longitude}&zoom=10&size=422x422"
        "&maptype=roadmap&markers={latitude},{longitude}&sensor=false"
        "&style=feature:poi|visibility:off&style=feature:poi.park|visibility:on"
    )

    def to_representation(self, value):
        try:
            latitude = value.latitude
            longitude = value.longitude
        except AttributeError:
            latitude = value.coords[1]
            longitude = value.coords[0]

        url = self.url.format(latitude=latitude, longitude=longitude)

        return staticmap_url_signer.sign_url(url)


class CountrySerializer(serializers.ModelSerializer):
    code = serializers.CharField(source='alpha2_code')
    oda = serializers.BooleanField(source='oda_recipient')

    class Meta(object):
        model = Country
        fields = ('id', 'name', 'code', 'oda')


class OfficeListSerializer(ModelSerializer):

    class Meta(object):
        model = Location
        fields = ('id', 'name', 'description', 'subregion')

    class JSONAPIMeta(object):
        resource_name = 'locations'
        included_resources = [
            'subregion',
            'subregion.region'
        ]

    included_serializers = {
        'subregion': 'bluebottle.offices.serializers.SubregionSerializer',
        'subregion.region': 'bluebottle.offices.serializers.RegionSerializer'
    }


class OfficeSerializer(ModelSerializer):
    latitude = serializers.DecimalField(source='position.latitude', required=False, max_digits=10, decimal_places=3)
    longitude = serializers.DecimalField(source='position.longitude', required=False, max_digits=10, decimal_places=3)
    image = ImageSerializer(required=False)

    static_map_url = StaticMapsField(source='position')

    class Meta(object):
        model = Location
        fields = (
            'id', 'name', 'description', 'image',
            'latitude', 'longitude', 'static_map_url',
            'subregion'
        )

    class JSONAPIMeta(object):
        resource_name = 'locations'
        included_resources = [
            'subregion',
            'subregion.region'
        ]

    included_serializers = {
        'subregion': 'bluebottle.offices.serializers.SubregionSerializer',
        'subregion.region': 'bluebottle.offices.serializers.RegionSerializer'
    }


class PlaceSerializer(ModelSerializer):
    position = PointSerializer(required=False, allow_null=True)

    class Meta(object):
        model = Place
        fields = (
            'id', 'street', 'street_number', 'postal_code',
            'locality', 'province', 'country', 'position', 'formatted_address',
            'mapbox_id'
        )

    class JSONAPIMeta(object):
        resource_name = 'places'
        included_resources = [
            'country',
        ]

    included_serializers = {
        'country': 'bluebottle.geo.serializers.InitiativeCountrySerializer',
    }


class SimplePointSerializer(serializers.CharField):

    def to_representation(self, instance):
        return [
            instance.coords[1],
            instance.coords[0]
        ]

    def to_internal_value(self, data):
        if not data:
            return None
        try:
            point = Point(float(data[1]), float(data[0]))
        except ValueError as e:
            raise serializers.ValidationError("Invalid point. {}".format(e))
        return point


class OldPlaceSerializer(serializers.ModelSerializer):
    position = SimplePointSerializer(required=False, allow_null=True)

    class Meta(object):
        model = Place
        fields = (
            'id', 'street', 'postal_code', 'street_number', 'locality', 'province', 'country',
            'position', 'formatted_address',
        )


class InitiativeCountrySerializer(ModelSerializer):
    code = serializers.CharField(source='alpha2_code')
    oda = serializers.BooleanField(source='oda_recipient')

    class Meta(object):
        model = Country
        fields = ('id', 'name', 'code', 'oda')

    class JSONAPIMeta(object):
        resource_name = 'countries'


class TinyPointSerializer(serializers.CharField):

    def to_representation(self, instance):
        if not hasattr(instance, 'coords'):
            return (instance.latitude, instance.longitude)
        else:
            return [instance.coords[1], instance.coords[0]]


class GeolocationSerializer(ModelSerializer):
    position = PointSerializer()
    static_map_url = StaticMapsField(source='position')
    timezone = serializers.ReadOnlyField()
    formatted_address = serializers.SerializerMethodField()
    locality = serializers.SerializerMethodField()

    def create(self, validated_data):
        mapbox_id = validated_data.get('mapbox_id')
        if mapbox_id:
            geolocation = Geolocation.objects.filter(mapbox_id=mapbox_id).first()
            if geolocation:
                return geolocation
        return super(GeolocationSerializer, self).create(validated_data)

    def get_formatted_address(self, obj):
        if obj.geofeature:
            return obj.geofeature.place_name
        return obj.formatted_address

    def get_locality(self, obj):
        if obj.geofeature:
            return obj.geofeature.name
        return obj.locality

    included_serializers = {
        'country': 'bluebottle.geo.serializers.InitiativeCountrySerializer'
    }

    class Meta(object):
        model = Geolocation
        fields = (
            'id',
            'street',
            'street_number',
            'locality',
            'province',
            'country',
            'position',
            'static_map_url',
            'formatted_address',
            'timezone',
            'mapbox_id'
        )

    class JSONAPIMeta(object):
        included_resources = [
            'country',
            'position'
        ]
        resource_name = 'geolocations'
