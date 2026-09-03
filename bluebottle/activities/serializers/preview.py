from datetime import date, datetime

import dateutil
from django.utils.timezone import get_current_timezone, now
from rest_framework import serializers

from bluebottle.geo.serializers import (
    card_location_parts_from_geofeatures,
    format_card_location,
    format_common_card_location,
)
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.utils.utils import get_current_language

LOCATION_TYPE_ORDER = (
    'location',
    'office',
    'place',
    'initiative_office',
    'impact_location',
)


def _as_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return dateutil.parser.parse(value).date()
    return value


def preview_slot_filters_from_request(request):
    """Parse optional slot filters from an activity-preview request."""
    if request is None:
        return False, None, None

    upcoming = request.GET.get('filter[upcoming]', '0') == '1'
    start = end = None
    tz = get_current_timezone()
    try:
        start, end = (
            dateutil.parser.parse(value).astimezone(tz)
            for value in request.GET.get('filter[date]').split(',')
        )
    except (TypeError, ValueError, AttributeError):
        pass
    return upcoming, start, end


class ActivityPreviewSlotSelection:
    def __init__(self, activity, upcoming=False, start=None, end=None):
        self.activity = activity
        self.upcoming = bool(upcoming)
        self.start = start
        self.end = end

    def get_slots(self):
        if not getattr(self.activity, 'slots', None):
            return []

        start = _as_date(self.start)
        end = _as_date(self.end)

        return [
            slot
            for slot in self.activity.slots
            if (
                slot.status not in ['draft', 'cancelled']
                and (
                    not self.upcoming
                    or datetime.fromisoformat(slot.start) >= now()
                )
                and (
                    not start
                    or _as_date(slot.start) >= start
                )
                and (
                    not end
                    or _as_date(slot.end) <= end
                )
            )
        ]

    def distinct_location_ids(self, slots=None):
        if slots is None:
            slots = self.get_slots()
        return {
            slot.location_id
            for slot in slots
            if getattr(slot, 'location_id', None)
        }


class ActivityPreviewSlottedLocationSerializer(serializers.Serializer):

    def _slot_selection(self, activity):
        return ActivityPreviewSlotSelection(
            activity,
            upcoming=self.context.get('upcoming', False),
            start=self.context.get('start'),
            end=self.context.get('end'),
        )

    def to_representation(self, activity):
        selection = self._slot_selection(activity)
        slots = selection.get_slots()

        if not slots:
            return None

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

    def _parts_for_slot(self, activity, slot, language):
        geofeatures = self._geofeatures_for_slot(slot, activity)
        return card_location_parts_from_geofeatures(activity, geofeatures, language)

    def _single_location(self, activity, slot):
        mode = InitiativePlatformSettings.load().card_location_display
        language = get_current_language()
        geofeatures = self._geofeatures_for_slot(slot, activity)

        return format_card_location(
            activity,
            mode,
            language,
            geofeatures=geofeatures,
        )

    def _multiple_locations(self, activity, slots):
        mode = InitiativePlatformSettings.load().card_location_display
        language = get_current_language()

        seen = {}
        for slot in slots:
            location_id = getattr(slot, 'location_id', None)
            if location_id and location_id not in seen:
                seen[location_id] = slot

        location_parts = [
            self._parts_for_slot(activity, slot, language)
            for slot in seen.values()
        ]

        return format_common_card_location(
            activity,
            mode,
            language,
            location_parts,
        )


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

        mode = InitiativePlatformSettings.load().card_location_display
        language = get_current_language()

        location = locations[0]
        location_geofeatures = getattr(location, 'geofeatures', None)
        activity_geofeatures = getattr(activity, 'geofeature', None)
        geofeatures = location_geofeatures or activity_geofeatures

        return format_card_location(
            activity,
            mode,
            language,
            geofeatures=geofeatures,
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
            activity,
            upcoming=self.context.get('upcoming', False),
            start=self.context.get('start'),
            end=self.context.get('end'),
        )
        slots = selection.get_slots()
        if len(selection.distinct_location_ids(slots)) <= 1:
            return False

        return self.to_representation(activity) is None
