from datetime import datetime

import dateutil
from django.utils.timezone import get_current_timezone, now
from rest_framework import serializers

from bluebottle.geo.mapbox import format_card_location, format_card_location_from_values
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


class ActivityPreviewSlottedLocationSerializer(serializers.Serializer):

    def to_representation(self, activity):
        slots = ActivityPreviewSlotSelection(
            activity, self.context['request']
        ).for_card()

        if len({slot.locality for slot in slots}) > 1:
            return None

        if not slots:
            return None

        slot = slots[0]
        mode = InitiativePlatformSettings.load().card_location_display
        language = get_current_language()

        slot_geofeatures = getattr(slot, 'geofeatures', None)
        activity_geofeatures = getattr(activity, 'geofeature', None)
        geofeatures = slot_geofeatures or activity_geofeatures

        formatted = format_card_location(
            activity,
            mode,
            language,
            geofeatures=geofeatures,
        )
        if formatted:
            return formatted

        if activity_geofeatures:
            formatted = format_card_location(
                activity,
                mode,
                language,
                geofeatures=activity_geofeatures,
            )
            if formatted:
                return formatted

        country = getattr(slot, 'country', None)
        country_name = None
        country_code = getattr(slot, 'country_code', None)
        if country is not None:
            country_name = getattr(country, 'name', country)
            if not country_code:
                country_code = getattr(country, 'alpha2_code', None)

        city = getattr(slot, 'locality', None)
        location_id = getattr(slot, 'location_id', None)
        if location_id and getattr(activity, 'location', None):
            for entry in activity.location:
                if getattr(entry, 'id', None) == location_id:
                    city = getattr(entry, 'locality', city)
                    break

        return format_card_location_from_values(
            mode,
            city=city,
            country=country_name,
            country_code=country_code,
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
