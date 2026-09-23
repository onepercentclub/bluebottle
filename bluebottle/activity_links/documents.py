from django.utils.timezone import now
from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry

from bluebottle.activities.documents import (
    ActivityDocument,
    activity,
    locality_from_geolocation,
)
from bluebottle.activity_links.models import LinkedDeed, LinkedFunding, LinkedActivity, LinkedDateActivity, \
    LinkedCollectCampaign, LinkedDeadlineActivity, LinkedPeriodicActivity, LinkedScheduleActivity, \
    LinkedGrantApplication, LinkedDateSlot
from bluebottle.initiatives.documents import deduplicate, get_translated_country_list
from bluebottle.time_based.documents import (
    deduplicate_locations,
    deduplicate_positions,
    slot_location_entry,
    unique_slot_geolocations,
)
from bluebottle.utils.documents import TextField
from bluebottle.utils.models import get_default_language


class LinkedActivityDocument(ActivityDocument):
    class Django:
        related_models = []
        model = LinkedActivity

    link = fields.KeywordField()

    def get_queryset(self):
        queryset = self.django.model._default_manager.all()
        if any(field.name == 'location' for field in self.django.model._meta.fields):
            queryset = queryset.select_related(
                'location',
                'location__country',
                'location__geofeature',
            ).prefetch_related(
                'location__geofeatures',
                'location__geofeatures__translations',
            )
        return queryset

    def prepare_is_local(self, instance):
        return False

    @classmethod
    def generate_id(cls, instance):
        return f"linked_{instance.pk}"

    def prepare_archived(self, instance):
        return instance.archived

    def prepare_current_status(self, instance):
        return {
            'value': 'open',
            'name': 'Open',
            'description': 'Open',
        }

    def prepare_link(self, instance):
        return instance.link

    def prepare_is_online(self, instance):
        return False
        location = getattr(instance, 'location', None)
        if location:
            return False
        return True

    def prepare_is_upcoming(self, instance):
        return instance.slots.filter(start__gte=now()).exists()

    def prepare_highlight(self, instance):
        return False

    def prepare_team_activity(self, instance):
        return 'individuals'

    def prepare_dates(self, instance):
        return [{
            'start': instance.start,
            'end': instance.end,
        }]

    # Override methods that don't apply to LinkedDeed
    def prepare_manager(self, instance):
        return []

    def prepare_contributors(self, instance):
        return []

    def prepare_contributor_count(self, instance):
        return 0

    def prepare_donation_count(self, instance):
        return 0

    def prepare_capacity(self, instance):
        return None

    def prepare_start(self, instance):
        return []

    def prepare_end(self, instance):
        return []

    def prepare_activity_date(self, instance):
        return []

    def prepare_image(self, instance):
        if instance.image:
            return {
                'id': instance.pk,
                'file': instance.image.file.name,
                'type': 'link'
            }
        return {}

    def prepare_owner(self, instance):
        return []

    def prepare_initiative(self, instance):
        return []

    def prepare_categories(self, instance):
        return []

    def prepare_country(self, instance):
        location = getattr(instance, 'location', None)
        if location and location.country:
            return get_translated_country_list(location.country)
        return []

    def prepare_expertise(self, instance):
        return []

    def prepare_segments(self, instance):
        return []

    def prepare_location(self, instance):
        location = getattr(instance, 'location', None)
        if not location:
            return []
        return [slot_location_entry(
            location,
            location_hint=getattr(instance, 'location_hint', None),
        )]

    def prepare_geofeature(self, instance):
        return []

    def prepare_position(self, instance):
        location = getattr(instance, 'location', None)
        if location and location.position:
            return [{'lat': location.position.y, 'lon': location.position.x}]
        return []

    def prepare_office(self, instance):
        return []

    def prepare_office_subregion(self, instance):
        return []

    def prepare_office_region(self, instance):
        return []

    def prepare_office_restriction(self, instance):
        return []

    def prepare_theme(self, instance):
        return []

    def prepare_slots(self, instance):
        return []

    def prepare_created(self, instance):
        return now()


@registry.register_document
@activity.doc_type
class LinkedDeedDocument(LinkedActivityDocument):
    class Django:
        model = LinkedDeed
        related_models = ()

    def prepare_slug(self, instance):
        return f'linked-deed-{instance.id}'

    def prepare_type(self, instance):
        return 'deed'

    def prepare_resource_name(self, instance):
        return 'activities/deeds'

    def prepare_activity_type(self, instance):
        return 'deed'

    def prepare_start(self, instance):
        return [instance.start]

    def prepare_end(self, instance):
        return [instance.end]


@registry.register_document
@activity.doc_type
class LinkedCollectCampaignDocument(LinkedActivityDocument):
    class Django:
        model = LinkedCollectCampaign
        related_models = ()

    collect_type = fields.NestedField(
        attr='collect_type',
        properties={
            'id': fields.KeywordField(),
            'name': fields.KeywordField(),
        }
    )

    realized = fields.IntegerField()
    collect_target = fields.IntegerField()

    def prepare_slug(self, instance):
        return f'linked-collect-{instance.id}'

    def prepare_type(self, instance):
        return 'collect'

    def prepare_resource_name(self, instance):
        return 'activities/collects'

    def prepare_activity_type(self, instance):
        return 'collect'

    def prepare_start(self, instance):
        return [instance.start]

    def prepare_end(self, instance):
        return [instance.end]

    def prepare_collect_type(self, instance):
        if not instance.collect_type:
            return []
        return [
            {'name': instance.collect_type, 'language': get_default_language()}
        ]


@registry.register_document
@activity.doc_type
class LinkedFundingDocument(LinkedActivityDocument):
    class Django:
        model = LinkedFunding
        related_models = ()

    target = fields.NestedField(properties={
        'currency': fields.KeywordField(),
        'amount': fields.FloatField(),
    })
    amount_raised = fields.NestedField(properties={
        'currency': fields.KeywordField(),
        'amount': fields.FloatField(),
    })

    def prepare_end(self, instance):
        return [instance.end]

    def prepare_slug(self, instance):
        return f'linked-funding-{instance.id}'

    def prepare_type(self, instance):
        return 'funding'

    def prepare_resource_name(self, instance):
        return 'activities/fundings'

    def prepare_activity_type(self, instance):
        return 'funding'

    def prepare_amount(self, amount):
        if amount:
            return {'amount': amount.amount, 'currency': str(amount.currency)}

    def prepare_target(self, instance):
        if not hasattr(instance, 'target'):
            return None
        return self.prepare_amount(instance.target)

    def prepare_amount_raised(self, instance):
        if not hasattr(instance, 'donated'):
            return None
        return self.prepare_amount(instance.donated)


@registry.register_document
@activity.doc_type
class LinkedGrantApplicationDocument(LinkedActivityDocument):
    class Django:
        model = LinkedGrantApplication
        related_models = ()

    target = fields.NestedField(properties={
        'currency': fields.KeywordField(),
        'amount': fields.FloatField(),
    })

    def prepare_end(self, instance):
        return [instance.end]

    def prepare_slug(self, instance):
        return f'linked-grant-application-{instance.id}'

    def prepare_type(self, instance):
        return 'grantapplication'

    def prepare_resource_name(self, instance):
        return 'activities/grant-applications'

    def prepare_activity_type(self, instance):
        return 'grantapplication'

    def prepare_amount(self, amount):
        if amount:
            return {'amount': amount.amount, 'currency': str(amount.currency)}

    def prepare_target(self, instance):
        if not hasattr(instance, 'target'):
            return None
        return self.prepare_amount(instance.target)


@registry.register_document
@activity.doc_type
class LinkedDateActivityDocument(LinkedActivityDocument):
    class Django:
        model = LinkedDateActivity
        related_models = (LinkedDateSlot,)

    slots = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'status': fields.KeywordField(),
        'title': TextField(),
        'start': fields.DateField(),
        'end': fields.DateField(),
        'location_hint': fields.KeywordField(),
        'locality': fields.KeywordField(),
        'formatted_address': fields.KeywordField(),
        'country_code': fields.KeywordField(),
        'country': fields.KeywordField(),
        'is_online': fields.BooleanField(),
        'location_id': fields.LongField(),
    })

    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            'slots',
            'slots__location',
            'slots__location__country',
            'slots__location__geofeature',
            'slots__location__geofeatures',
            'slots__location__geofeatures__translations',
        )

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, LinkedDateSlot):
            return related_instance.activity

    def prepare_is_online(self, instance):
        return False

    def prepare_slots(self, instance):
        slots = []
        for slot in instance.slots.all():
            location = slot.location
            if location:
                country = location.country
                locality = locality_from_geolocation(location)
                formatted_address = (
                    location.geofeature.place_name
                    if location.geofeature else location.formatted_address
                )
                location_id = location.id
            else:
                country = None
                locality = None
                formatted_address = None
                location_id = None
            slots.append({
                'id': str(slot.pk),
                'status': slot.status,
                'title': '',
                'start': slot.start,
                'end': slot.end,
                'location_hint': None,
                'locality': locality,
                'formatted_address': formatted_address,
                'country': country.name if country else None,
                'country_code': country.alpha2_code if country else None,
                'is_online': False,
                'location_id': location_id,
            })
        return slots

    def prepare_location(self, instance):
        locations = [
            slot_location_entry(geolocation)
            for geolocation in unique_slot_geolocations(instance.slots.all())
        ]
        return deduplicate_locations(locations)

    def prepare_country(self, instance):
        countries = []
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

    def prepare_start(self, instance):
        return [slot.start for slot in instance.slots.all()]

    def prepare_end(self, instance):
        return [slot.end for slot in instance.slots.all()]

    def prepare_dates(self, instance):
        return [
            {
                'start': slot.start,
                'end': slot.end,
            }
            for slot in instance.slots.all()
            if slot.start and slot.end
        ]

    def prepare_duration(self, instance):
        return [
            {'gte': slot.start, 'lte': slot.end}
            for slot in instance.slots.all()
            if slot.start and slot.duration
        ]

    def prepare_contribution_duration(self, instance):
        return [
            {
                'period': 'slot',
                'start': slot.start,
                'value': slot.duration.seconds / (60 * 60) + slot.duration.days * 24
            }
            for slot in instance.slots.all()
            if slot.start and slot.duration
        ]

    def prepare_slug(self, instance):
        return f'linked-date-{instance.id}'

    def prepare_type(self, instance):
        return 'date'

    def prepare_resource_name(self, instance):
        return 'activities/time-based/dates'

    def prepare_activity_type(self, instance):
        return 'date'


@registry.register_document
@activity.doc_type
class LinkedDeadlineActivityDocument(LinkedActivityDocument):
    contribution_duration = fields.NestedField(properties={
        'period': fields.KeywordField(),
        'value': fields.FloatField()
    })

    class Django:
        model = LinkedDeadlineActivity
        related_models = ()

    def prepare_start(self, instance):
        return [instance.start]

    def prepare_end(self, instance):
        return [instance.end]

    def prepare_dates(self, instance):
        return [
            {
                'start': instance.start,
                'end': instance.end,
            }
        ]

    def prepare_duration(self, instance):
        if instance.start and instance.end and instance.start > instance.end:
            return {}
        return {"gte": instance.start, "lte": instance.end}

    def prepare_contribution_duration(self, instance):
        if instance.duration:
            return [{
                'period': 'once',
                'start': instance.start,
                'value': instance.duration.seconds / (60 * 60) + instance.duration.days * 24
            }]
        return [{
            'start': instance.start,
            'value': 0,
            'period': 0,
        }]

    def prepare_slug(self, instance):
        return f'linked-deadline-{instance.id}'

    def prepare_type(self, instance):
        return 'deadline'

    def prepare_resource_name(self, instance):
        return 'activities/time-based/deadlines'

    def prepare_activity_type(self, instance):
        return 'deadline'


@registry.register_document
@activity.doc_type
class LinkedScheduleActivityDocument(LinkedActivityDocument):
    contribution_duration = fields.NestedField(properties={
        'period': fields.KeywordField(),
        'value': fields.FloatField()
    })

    class Django:
        model = LinkedScheduleActivity
        related_models = ()

    def prepare_start(self, instance):
        return [instance.start]

    def prepare_end(self, instance):
        return [instance.end]

    def prepare_dates(self, instance):
        return [
            {
                'start': instance.start,
                'end': instance.end,
            }
        ]

    def prepare_duration(self, instance):
        if instance.start and instance.end and instance.start > instance.end:
            return {}
        return {"gte": instance.start, "lte": instance.end}

    def prepare_contribution_duration(self, instance):
        if instance.duration:
            return [{
                'period': 'once',
                'start': instance.start,
                'value': instance.duration.seconds / (60 * 60) + instance.duration.days * 24
            }]
        return [{
            'start': instance.start,
            'value': 0,
            'period': 0,
        }]

    def prepare_slug(self, instance):
        return f'linked-schedule-{instance.id}'

    def prepare_type(self, instance):
        return 'schedule'

    def prepare_resource_name(self, instance):
        return 'activities/time-based/schedules'

    def prepare_activity_type(self, instance):
        return 'schedule'


@registry.register_document
@activity.doc_type
class LinkedPeriodicActivityDocument(LinkedActivityDocument):
    contribution_duration = fields.NestedField(properties={
        'period': fields.KeywordField(),
        'value': fields.FloatField()
    })

    class Django:
        model = LinkedPeriodicActivity
        related_models = ()

    def prepare_start(self, instance):
        return [instance.start]

    def prepare_end(self, instance):
        return [instance.end]

    def prepare_dates(self, instance):
        return [
            {
                'start': instance.start,
                'end': instance.end,
            }
        ]

    def prepare_duration(self, instance):
        if instance.start and instance.end and instance.start > instance.end:
            return {}
        return {"gte": instance.start, "lte": instance.end}

    def prepare_contribution_duration(self, instance):
        if instance.duration:
            return [
                {
                    'period': instance.period,
                    'value': instance.duration.seconds / (60 * 60) + instance.duration.days * 24
                }
            ]

    def prepare_slug(self, instance):
        return f'linked-periodic-{instance.id}'

    def prepare_type(self, instance):
        return 'periodic'

    def prepare_resource_name(self, instance):
        return 'activities/time-based/periodics'

    def prepare_activity_type(self, instance):
        return 'periodic'
