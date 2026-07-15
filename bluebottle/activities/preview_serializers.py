from datetime import datetime

import dateutil
from django.utils.timezone import get_current_timezone, now
from rest_framework import serializers

from bluebottle.geo.mapbox import (
    card_location_parts_from_entry,
    card_location_parts_from_geofeatures,
    format_card_location,
    format_card_location_from_values,
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

    def visible(self, only_upcoming=False):
        if not getattr(self.activity, 'slots', None):
            return []

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

    def for_card(self):
        upcoming = self.visible(only_upcoming=True)
        if upcoming:
            return upcoming
        return self.visible(only_upcoming=False)

    def distinct_location_ids(self, slots=None):
        slots = slots if slots is not None else self.for_card()
        return {
            slot.location_id
            for slot in slots
            if getattr(slot, 'location_id', None)
        }


class ActivityPreviewSlottedLocationSerializer(serializers.Serializer):

    def to_representation(self, activity):
        slots = ActivityPreviewSlotSelection(
            activity, self.context['request']
        ).for_card()

        if not slots:
            return None

        selection = ActivityPreviewSlotSelection(activity, self.context['request'])
        if len(selection.distinct_location_ids(slots)) <= 1:
            return self._single_location(activity, slots[0])

        return self._multiple_locations(activity, slots)

    def _location_entry(self, activity, location_id):
        if not location_id or not getattr(activity, 'location', None):
            return None

        for entry in activity.location:
            if getattr(entry, 'id', None) == location_id:
                return entry

    def _geofeatures_for_slot(self, slot, activity):
        geofeatures = getattr(slot, 'geofeatures', None) or []
        if geofeatures:
            return geofeatures

        entry = self._location_entry(activity, getattr(slot, 'location_id', None))
        if entry:
            entry_geofeatures = getattr(entry, 'geofeatures', None) or []
            if entry_geofeatures:
                return entry_geofeatures

        return getattr(activity, 'geofeature', None) or []

    def _parts_for_slot(self, activity, slot, language):
        geofeatures = self._geofeatures_for_slot(slot, activity)
        parts = card_location_parts_from_geofeatures(activity, geofeatures, language)
        if parts:
            return parts

        entry = self._location_entry(activity, getattr(slot, 'location_id', None))
        if entry:
            return card_location_parts_from_entry(entry)

        return card_location_parts_from_entry(slot)

    def _single_location(self, activity, slot):
        mode = InitiativePlatformSettings.load().card_location_display
        language = get_current_language()
        geofeatures = self._geofeatures_for_slot(slot, activity)

        formatted = format_card_location(
            activity,
            mode,
            language,
            geofeatures=geofeatures,
        )
        if formatted:
            return formatted

        parts = self._parts_for_slot(activity, slot, language)
        return format_card_location_from_values(
            mode,
            city=parts.get('city'),
            region=parts.get('region'),
            neighborhood=parts.get('neighborhood'),
            locality=parts.get('locality'),
            country=parts.get('country'),
            country_code=parts.get('country_code'),
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
        if activity.type == 'funding':
            locations = [
                location for location in activity.location
                if location.type in ('impact_location', 'location')
            ]
        elif activity.location:
            locations = sorted(
                activity.location,
                key=lambda loc: LOCATION_TYPE_ORDER.index(
                    getattr(loc, 'type', 'location')
                ),
            )
        else:
            return None

        if not locations:
            return None

        location = locations[0]
        mode = InitiativePlatformSettings.load().card_location_display
        language = get_current_language()

        location_geofeatures = getattr(location, 'geofeatures', None)
        activity_geofeatures = getattr(activity, 'geofeature', None)
        geofeatures = location_geofeatures or activity_geofeatures

        formatted = format_card_location(
            activity,
            mode,
            language,
            geofeatures=geofeatures,
        )
        if formatted:
            return formatted

        country = getattr(location, 'country', None)
        country_name = None
        country_code = getattr(location, 'country_code', None)
        if country is not None:
            country_name = getattr(country, 'name', country)
            if not country_code:
                country_code = getattr(country, 'alpha2_code', None)

        return format_card_location_from_values(
            mode,
            city=getattr(location, 'locality', None),
            country=country_name,
            country_code=country_code,
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
        slots = selection.for_card()
        if len(selection.distinct_location_ids(slots)) <= 1:
            return False

        return self.to_representation(activity) is None
