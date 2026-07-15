from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry

from bluebottle.activities.documents import ActivityDocument, activity, get_translated_country_list
from bluebottle.geo.mapbox import get_translated_geofeature_list, locality_from_geolocation
from bluebottle.time_based.models import (
    DateActivity,
    DeadlineActivity,
    DeadlineParticipant,
    PeriodicActivity,
    PeriodicParticipant,
    ScheduleActivity,
    ScheduleParticipant,
    DateParticipant,
    DateActivitySlot,
    RegisteredDateActivity,
    RegisteredDateParticipant
)
from bluebottle.utils.documents import TextField

SCORE_MAP = {
    'open': 1,
    'running': 0.7,
    'full': 0.6,
    'succeeded': 0.5,
}


class TimeBasedActivityDocument(ActivityDocument):

    def prepare_status_score(self, instance):
        return SCORE_MAP.get(instance.status, 0)


def deduplicate(items):
    return [dict(s) for s in set(frozenset(d.items()) for d in items)]


def unique_slot_geolocations(slots):
    seen = {}
    for slot in slots:
        if slot.is_online or not slot.location_id:
            continue
        if slot.location_id not in seen:
            seen[slot.location_id] = slot.location
    return list(seen.values())


def deduplicate_locations(locations):
    seen = {}
    for location in locations:
        location_id = location.get('id')
        if location_id is not None:
            key = ('id', location_id)
        else:
            key = (
                'address',
                location.get('name'),
                location.get('locality'),
                location.get('country_code'),
                location.get('type'),
            )
        if key not in seen:
            seen[key] = location
    return list(seen.values())


def deduplicate_positions(positions):
    seen = {}
    for position in positions:
        key = (position.get('lat'), position.get('lon'))
        if key not in seen:
            seen[key] = position
    return list(seen.values())


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


def slot_location_entry(geolocation, location_hint=None):
    primary = geolocation.geofeature
    country = geolocation.country
    return {
        'id': geolocation.id,
        'name': primary.place_name if primary else geolocation.formatted_address,
        'formatted_address': primary.place_name if primary else geolocation.formatted_address,
        'location_hint': location_hint,
        'locality': locality_from_geolocation(geolocation),
        'country_code': country.alpha2_code if country else None,
        'country': country.name if country else None,
        'type': 'location',
        'geofeatures': geofeatures_for_geolocation(geolocation),
    }


@registry.register_document
@activity.document
class DateActivityDocument(TimeBasedActivityDocument):
    contribution_duration = fields.NestedField(properties={
        'value': fields.FloatField()
    })

    slots = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'status': fields.KeywordField(),
        'title': TextField(),
        'start': fields.DateField(),
        'end': fields.DateField(),
        'location_hint': fields.KeywordField(),
        'locality': fields.KeywordField(),
        'formatted_address': fields.KeywordField(),
        'country_code': fields.KeywordField(attr='location.country.alpha2_code'),
        'country': fields.KeywordField(attr='location.country.name'),
        'is_online': fields.BooleanField(),
        'location_id': fields.LongField(),
        'geofeatures': fields.NestedField(properties={
            'id': fields.LongField(),
            'name': TextField(),
            'mapbox_id': fields.KeywordField(),
            'place_name': TextField(),
            'language': fields.KeywordField(),
            'feature_type': fields.KeywordField(),
            'is_primary': fields.BooleanField(),
            'country': TextField(),
            'country_code': TextField(),
        }),
    })

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.prefetch_related(
            'slots',
            'slots__location',
            'slots__location__country',
            'slots__location__geofeature',
            'slots__location__geofeatures',
            'slots__location__geofeatures__translations',
        )
        return queryset

    def get_instances_from_related(self, related_instance):
        result = super().get_instances_from_related(related_instance)

        if result is not None:
            return result

        if isinstance(related_instance, DateParticipant):
            return DateActivity.objects.filter(contributors=related_instance)
        if isinstance(related_instance, DateActivitySlot):
            return related_instance.activity

    class Django:
        related_models = ActivityDocument.Django.related_models + (DateParticipant, DateActivitySlot)
        model = DateActivity

    def prepare_location(self, instance):
        locations = super(DateActivityDocument, self).prepare_location(instance)
        for geolocation in unique_slot_geolocations(instance.slots.all()):
            locations.append(slot_location_entry(geolocation))
        return deduplicate_locations(locations)

    def prepare_geofeature(self, instance):
        geofeatures = []
        for geolocation in unique_slot_geolocations(instance.slots.all()):
            geofeatures.extend(geofeatures_for_geolocation(geolocation))
        return deduplicate(geofeatures)

    def prepare_slots(self, instance):
        slots = []
        for slot in instance.active_slots.all():
            location = slot.location
            if not location:
                continue

            country = location.country
            slots.append({
                'id': str(slot.pk),
                'status': slot.status,
                'title': slot.title,
                'start': slot.start,
                'end': slot.end,
                'location_hint': slot.location_hint,
                'locality': locality_from_geolocation(location),
                'formatted_address': (
                    location.geofeature.place_name
                    if location.geofeature else location.formatted_address
                ),
                'country': country.name if country else None,
                'country_code': country.alpha2_code if country else None,
                'is_online': slot.is_online,
                'location_id': location.id,
                'geofeatures': geofeatures_for_geolocation(location),
            })
        return slots

    def prepare_start(self, instance):
        return [slot.start for slot in instance.slots.all() if slot.status in ('open', 'full', 'finished', )]

    def prepare_end(self, instance):
        return [
            slot.start + slot.duration
            for slot in instance.slots.all()
            if slot.start and slot.duration and slot.status in ('open', 'full', 'finished', )
        ]

    def prepare_dates(self, instance):
        return [
            {
                'start': slot.start,
                'end': slot.start + slot.duration,
                'status': slot.status
            }
            for slot in instance.slots.all()
            if slot.start and slot.duration and slot.status in ('open', 'full', 'finished', )
        ]

    def prepare_duration(self, instance):
        return [
            {'gte': slot.start, 'lte': slot.end}
            for slot in instance.slots.all()
            if slot.start and slot.duration and slot.status in ('open', 'full', 'finished')
        ]

    def prepare_contribution_duration(self, instance):
        return [
            {
                'period': 'slot',
                'start': slot.start,
                'value': slot.duration.seconds / (60 * 60) + slot.duration.days * 24
            }
            for slot in instance.slots.all()
            if slot.start and slot.duration and slot.status in ('open', 'full', 'finished')
        ]

    def prepare_country(self, instance):
        countries = super().prepare_country(instance)
        for geolocation in unique_slot_geolocations(instance.slots.all()):
            if geolocation.country:
                countries += get_translated_country_list(geolocation.country)
        return deduplicate(countries)

    def prepare_position(self, instance):
        positions = [
            {'lat': geolocation.position.y, 'lon': geolocation.position.x}
            for geolocation in unique_slot_geolocations(instance.slots.all())
            if geolocation.position
        ]
        return deduplicate_positions(positions)

    def prepare_is_online(self, instance):
        return any(slot.is_online for slot in instance.slots.all())


class RegistrationActivityDocument(TimeBasedActivityDocument):

    contribution_duration = fields.NestedField(properties={
        'period': fields.KeywordField(),
        'value': fields.FloatField()
    })

    def get_instances_from_related(self, related_instance):
        result = super().get_instances_from_related(related_instance)

        if result is not None:
            return result

        if isinstance(related_instance, self.participant_class):
            return DeadlineActivity.objects.filter(contributors=related_instance)

    def prepare_contribution_duration(self, instance):

        if instance.duration:
            return [{
                'period': 0,
                'start': instance.start,
                'value': instance.duration.seconds / (60 * 60) + instance.duration.days * 24
            }]
        return [{
            'start': instance.start,
            'value': 0,
            'period': 0,
        }]

    def prepare_country(self, instance):
        countries = super().prepare_country(instance)
        if instance.location and instance.location.country:
            countries += get_translated_country_list(instance.location.country)

        return deduplicate(countries)

    def prepare_position(self, instance):
        if not instance.is_online and instance.location:
            position = instance.location.position
            return [{'lat': position.y, 'lon': position.x}]

    def prepare_start(self, instance):
        return [instance.start]

    def prepare_end(self, instance):
        return [instance.deadline]

    def prepare_dates(self, instance):
        return [{
            'start': instance.start,
            'end': instance.deadline
        }]

    def prepare_duration(self, instance):
        if instance.start and instance.deadline and instance.start > instance.deadline:
            return {}
        return {"gte": instance.start, "lte": instance.deadline}


@registry.register_document
@activity.doc_type
class DeadlineActivityDocument(RegistrationActivityDocument):
    participant_class = DeadlineParticipant

    def prepare_contribution_duration(self, instance):
        if instance.duration:
            return [
                {
                    'period': 'once',
                    'value': instance.duration.seconds / (60 * 60) + instance.duration.days * 24
                }
            ]

    class Django:
        related_models = ActivityDocument.Django.related_models + (DeadlineParticipant,)
        model = DeadlineActivity


@registry.register_document
@activity.doc_type
class PeriodicActivityDocument(RegistrationActivityDocument):
    participant_class = PeriodicParticipant

    def prepare_contribution_duration(self, instance):
        if instance.duration:
            return [
                {
                    'period': instance.period,
                    'value': instance.duration.seconds / (60 * 60) + instance.duration.days * 24
                }
            ]

    class Django:

        related_models = ActivityDocument.Django.related_models + (PeriodicParticipant,)
        model = PeriodicActivity


@registry.register_document
@activity.doc_type
class ScheduleActivityDocument(RegistrationActivityDocument):
    participant_class = ScheduleParticipant

    def prepare_country(self, instance):
        countries = super().prepare_country(instance)
        if instance.location and instance.location.country:
            countries += get_translated_country_list(instance.location.country)

        return deduplicate(countries)

    def prepare_contribution_duration(self, instance):
        if instance.duration:
            return [
                {
                    'period': 'once',
                    'value': instance.duration.seconds / (60 * 60) + instance.duration.days * 24
                }
            ]

    class Django:

        related_models = ActivityDocument.Django.related_models + (ScheduleParticipant,)
        model = ScheduleActivity


@registry.register_document
@activity.doc_type
class RegisteredActivityDocument(RegistrationActivityDocument):
    participant_class = RegisteredDateParticipant

    def prepare_contribution_duration(self, instance):
        if instance.duration:
            return [
                {
                    'period': 'once',
                    'value': instance.duration.seconds / (60 * 60) + instance.duration.days * 24
                }
            ]

    class Django:
        related_models = ActivityDocument.Django.related_models + (RegisteredDateParticipant,)
        model = RegisteredDateActivity

    def prepare_position(self, instance):
        return []

    def prepare_start(self, instance):
        return [instance.start]

    def prepare_end(self, instance):
        return [instance.start]

    def prepare_dates(self, instance):
        return [{
            'start': instance.start,
            'end': instance.start
        }]

    def prepare_duration(self, instance):
        return {"gte": instance.start, "lte": instance.start}
