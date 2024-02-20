from datetime import datetime

from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry

from bluebottle.activities.documents import ActivityDocument, activity, get_translated_list
from bluebottle.time_based.models import (
    DateActivity, DeadlineActivity, DeadlineParticipant, PeriodActivity, DateParticipant, PeriodParticipant,
    DateActivitySlot, DeadlineActivity
)

SCORE_MAP = {
    'open': 1,
    'running': 0.7,
    'full': 0.6,
    'succeeded': 0.5,
}


class TimeBasedActivityDocument:

    def prepare_status_score(self, instance):
        return SCORE_MAP.get(instance.status, 0)


def deduplicate(items):
    return [dict(s) for s in set(frozenset(d.items()) for d in items)]


@registry.register_document
@activity.document
class DateActivityDocument(TimeBasedActivityDocument, ActivityDocument):
    contribution_duration = fields.NestedField(properties={
        'value': fields.FloatField()
    })

    slots = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'status': fields.KeywordField(),
        'title': fields.TextField(),
        'start': fields.DateField(),
        'end': fields.DateField(),
        'locality': fields.KeywordField(attr='location.locality'),
        'formatted_address': fields.KeywordField(attr='location.formatted_address'),
        'country_code': fields.KeywordField(attr='location.country.alpha2_code'),
        'country': fields.KeywordField(attr='location.country.name'),
        'is_online': fields.BooleanField(),
    })

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

    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            'slots'
        )

    def prepare_location(self, instance):
        locations = super(DateActivityDocument, self).prepare_location(instance)
        locations += [
            {
                'name': slot.location.formatted_address,
                'locality': slot.location.locality,
                'country_code': slot.location.country.alpha2_code,
                'country': slot.location.country.name
            }
            for slot in instance.slots.all()
            if not slot.is_online and slot.location
        ]
        return locations

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
        for slot in instance.slots.all():
            if not slot.is_online and slot.location and slot.location.country:
                countries += get_translated_list(slot.location.country)
        return deduplicate(countries)

    def prepare_position(self, instance):
        return [
            {'lat': slot.location.position.y, 'lon': slot.location.position.x}
            for slot in instance.slots.all()
            if not slot.is_online and slot.location and slot.location.position
        ]

    def prepare_is_online(self, instance):
        return any(slot.is_online for slot in instance.slots.all())


@registry.register_document
@activity.doc_type
class PeriodActivityDocument(TimeBasedActivityDocument, ActivityDocument):
    contribution_duration = fields.NestedField(properties={
        'period': fields.KeywordField(),
        'value': fields.FloatField()
    })

    def get_instances_from_related(self, related_instance):
        result = super().get_instances_from_related(related_instance)

        if result is not None:
            return result

        if isinstance(related_instance, PeriodParticipant):
            return PeriodActivity.objects.filter(contributors=related_instance)

    class Django:
        related_models = ActivityDocument.Django.related_models + (PeriodParticipant, )
        model = PeriodActivity

    def prepare_contribution_duration(self, instance):
        if instance.duration:
            return [{
                'period': instance.duration_period,
                'start': instance.start,
                'value': instance.duration.seconds / (60 * 60) + instance.duration.days * 24
            }]
        return [{
            'period': instance.duration_period,
            'start': instance.start,
            'value': 0
        }]

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
            'start': instance.start or datetime.min,
            'end': instance.deadline or datetime.max,
        }]

    def prepare_duration(self, instance):
        if instance.start and instance.deadline and instance.start > instance.deadline:
            return {}

        return {'gte': instance.start, 'lte': instance.deadline}


@registry.register_document
@activity.doc_type
class DeadlinectivityDocument(TimeBasedActivityDocument, ActivityDocument):
    contribution_duration = fields.NestedField(properties={
        'period': fields.KeywordField(),
        'value': fields.FloatField()
    })

    def get_instances_from_related(self, related_instance):
        result = super().get_instances_from_related(related_instance)

        if result is not None:
            return result

        if isinstance(related_instance, DeadlineParticipant):
            return PeriodActivity.objects.filter(contributors=related_instance)

    class Django:
        related_models = ActivityDocument.Django.related_models + (DeadlineParticipant, )
        model = DeadlineActivity

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
            'start': instance.start or datetime.min,
            'end': instance.deadline or datetime.max,
        }]

    def prepare_duration(self, instance):
        if instance.start and instance.deadline and instance.start > instance.deadline:
            return {}

        return {'gte': instance.start, 'lte': instance.deadline}
