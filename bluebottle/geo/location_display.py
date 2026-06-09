from __future__ import annotations

from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.utils.utils import get_current_language

GEOFEATURE_PLACE_TYPE_ALIASES = {
    'neighborhood': ('neighborhou', 'neighborhood'),
    'address': ('address', 'street', 'secondary_address'),
}


def indexed_field(obj, attribute, default=None):
    """Read a field from a dict or an Elasticsearch ``AttrDict`` hit."""
    if isinstance(obj, dict):
        return obj.get(attribute, default)
    return getattr(obj, attribute, default)


def _is_geofeature_model(feature):
    return callable(getattr(feature, 'set_current_language', None))


def _feature_value(feature, attribute):
    return indexed_field(feature, attribute)


def _features_for_language(geofeatures, language):
    if not geofeatures:
        return []
    if not _is_geofeature_model(geofeatures[0]):
        translated = [
            feature for feature in geofeatures
            if _feature_value(feature, 'language') == language
        ]
        return translated or list(geofeatures)
    for feature in geofeatures:
        feature.set_current_language(language)
    return list(geofeatures)


def _match_geofeature(features, place_type):
    place_types = GEOFEATURE_PLACE_TYPE_ALIASES.get(place_type, (place_type,))
    for candidate_type in place_types:
        match = next(
            (feature for feature in features if _feature_value(feature, 'place_type') == candidate_type),
            None,
        )
        if match:
            return match
    return None


def _append_part(parts, value):
    if value and (not parts or parts[-1] != value):
        parts.append(str(value))


def format_location_display(
    geofeatures,
    *,
    locality=None,
    formatted_address=None,
    location_features=None,
    language=None,
):
    """Return a comma-separated location line for activity cards and previews."""
    if not geofeatures and not locality and not formatted_address:
        return None

    if location_features is None:
        location_features = InitiativePlatformSettings.load().location_features

    language = language or get_current_language()
    features = _features_for_language(geofeatures or [], language)

    parts = []
    for feature_key in location_features:
        if feature_key == 'location_name':
            _append_part(parts, locality)
            continue

        if feature_key == 'address':
            match = _match_geofeature(features, 'address')
            if match:
                _append_part(
                    parts,
                    _feature_value(match, 'place_name') or _feature_value(match, 'name'),
                )
            else:
                _append_part(parts, formatted_address)
            continue

        match = _match_geofeature(features, feature_key)
        if not match:
            continue
        if feature_key == 'country':
            _append_part(parts, _feature_value(match, 'code') or _feature_value(match, 'name'))
        else:
            _append_part(parts, _feature_value(match, 'name'))

    return ', '.join(parts) if parts else None


def format_geolocation_display(geolocation, location_features=None, language=None):
    """Format a ``Geolocation`` model using platform location display settings."""
    if not geolocation:
        return None
    return format_location_display(
        geolocation.features.all(),
        locality=geolocation.locality,
        formatted_address=geolocation.formatted_address,
        location_features=location_features,
        language=language,
    )
