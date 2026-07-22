from datetime import datetime

import dateutil
from django.utils.timezone import get_current_timezone, now
from rest_framework import serializers

from bluebottle.geo.mapbox import FEATURE_TYPE_HIERARCHY
from bluebottle.utils.utils import get_current_language

LOCATION_TYPE_ORDER = (
    'location',
    'office',
    'place',
    'initiative_office',
    'impact_location',
)


def _attr(entry, key, default=None):
    if entry is None:
        return default
    if isinstance(entry, dict):
        return entry.get(key, default)
    return getattr(entry, key, default)


def _entries_for_language(entries, language):
    if not isinstance(language, str):
        language = 'en'

    matched = [
        entry for entry in entries
        if _attr(entry, 'language') == language
    ]
    if matched:
        return matched

    prefix = language.split('-')[0]
    return [
        entry for entry in entries
        if _attr(entry, 'language', '').startswith(prefix)
    ]


def place_name_from_preview_geofeatures(geofeatures, language=None):
    language = (language or get_current_language() or 'en').split(',')[0]
    entries = _entries_for_language(geofeatures or [], language)
    if not entries:
        return None

    primary = next(
        (entry for entry in entries if _attr(entry, 'is_primary')),
        None,
    )
    if primary:
        return _attr(primary, 'place_name') or _attr(primary, 'name')

    for feature_type in FEATURE_TYPE_HIERARCHY:
        match = next(
            (
                entry for entry in entries
                if _attr(entry, 'feature_type') == feature_type
            ),
            None,
        )
        if match:
            return _attr(match, 'place_name') or _attr(match, 'name')

    return _attr(entries[0], 'place_name') or _attr(entries[0], 'name')


def common_place_name_from_preview_geofeature_groups(groups, language=None):
    language = (language or get_current_language() or 'en').split(',')[0]
    feature_maps = []
    for geofeatures in groups:
        entries = _entries_for_language(geofeatures or [], language)
        by_type = {}
        for entry in entries:
            feature_type = _attr(entry, 'feature_type')
            name = _attr(entry, 'place_name') or _attr(entry, 'name')
            if feature_type and name:
                by_type[feature_type] = name
        feature_maps.append(by_type)

    if not feature_maps:
        return None

    for feature_type in FEATURE_TYPE_HIERARCHY:
        values = [feature_map.get(feature_type) for feature_map in feature_maps]
        if any(value is None for value in values):
            continue
        if len(set(values)) == 1:
            return values[0]
    return None


class ActivityPreviewSlotSelection:
    def __init__(self, activity, request):
        self.activity = activity
        self.request = request

    def date_range(self):
        tz = get_current_timezone()
        try:
            start, end = (
                dateutil.parser.parse(date).astimezone(tz)
                for date in self.request.GET.get('filter[date]').split(',')
            )
        except (ValueError, AttributeError):
            return None, None
        return start, end

    def get_slots(self):
        if not getattr(self.activity, 'slots', None):
            return []
        only_upcoming = self.request.GET.get('upcoming', False)
        start, end = self.date_range()

        return [
            slot
            for slot in self.activity.slots
            if (
                slot.status not in ['draft', 'cancelled']
                and (
                    not only_upcoming
                    or datetime.fromisoformat(slot.start) >= now()
                )
                and (
                    not start
                    or dateutil.parser.parse(slot.start).date() >= start.date()
                )
                and (
                    not end
                    or dateutil.parser.parse(slot.end).date() <= end.date()
                )
            )
        ]

    def distinct_location_ids(self, slots=None):
        slots = self.get_slots()
        return {
            slot.location_id
            for slot in slots
            if getattr(slot, 'location_id', None)
        }


class ActivityPreviewSlottedLocationSerializer(serializers.Serializer):

    def to_representation(self, activity):
        slots = ActivityPreviewSlotSelection(
            activity, self.context['request']
        ).get_slots()

        if not slots:
            return None

        selection = ActivityPreviewSlotSelection(activity, self.context['request'])
        if len(selection.distinct_location_ids(slots)) <= 1:
            return self._single_location(activity, slots[0])

        return self._multiple_locations(activity, slots)

    def _geofeatures_for_slot(self, slot, activity):
        geofeatures = getattr(slot, 'geofeatures', None) or []
        if geofeatures:
            return geofeatures

        if not getattr(activity, 'location', None):
            return getattr(activity, 'geofeature', None) or []

        location_id = getattr(slot, 'location_id', None)
        if location_id:
            for entry in activity.location:
                if getattr(entry, 'id', None) == location_id:
                    entry_geofeatures = getattr(entry, 'geofeatures', None) or []
                    if entry_geofeatures:
                        return entry_geofeatures
                    break

        return getattr(activity, 'geofeature', None) or []

    def _single_location(self, activity, slot):
        return place_name_from_preview_geofeatures(
            self._geofeatures_for_slot(slot, activity),
        )

    def _multiple_locations(self, activity, slots):
        seen = {}
        for slot in slots:
            location_id = getattr(slot, 'location_id', None)
            if location_id and location_id not in seen:
                seen[location_id] = slot

        return common_place_name_from_preview_geofeature_groups([
            self._geofeatures_for_slot(slot, activity)
            for slot in seen.values()
        ])


class ActivityPreviewSingleLocationSerializer(serializers.Serializer):

    def to_representation(self, activity):
        location_types = (
            'location',
            'office',
            'place',
            'initiative_office',
            'impact_location',
        )
        if activity.type == 'funding':
            location_types = ('impact_location', 'location', 'office', 'initiative_office')

        locations = []

        for location_type in location_types:
            for loc in activity.location:
                if loc.type == location_type:
                    locations.append(loc)

        if not locations:
            return None

        location = locations[0]
        location_geofeatures = getattr(location, 'geofeatures', None)
        activity_geofeatures = getattr(activity, 'geofeature', None)
        return place_name_from_preview_geofeatures(
            location_geofeatures or activity_geofeatures,
        )


class ActivityPreviewLocationSerializer(serializers.Serializer):

    def to_representation(self, activity):
        if getattr(activity, 'slots', None):
            return ActivityPreviewSlottedLocationSerializer(
                context=self.context,
            ).to_representation(activity)

        return ActivityPreviewSingleLocationSerializer(
            context=self.context,
        ).to_representation(activity)

    def has_multiple_unresolved_locations(self, activity):
        if not getattr(activity, 'slots', None):
            return False

        selection = ActivityPreviewSlotSelection(
            activity, self.context['request']
        )
        slots = selection.get_slots()
        if len(selection.distinct_location_ids(slots)) <= 1:
            return False

        return self.to_representation(activity) is None
