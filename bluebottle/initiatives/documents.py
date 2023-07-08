from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from bluebottle.activities.models import Activity
from bluebottle.categories.models import Category
from bluebottle.deeds.models import Deed
from bluebottle.funding.models import Funding
from bluebottle.geo.models import Geolocation
from bluebottle.initiatives.models import Initiative, Theme
from bluebottle.time_based.models import PeriodActivity, DateActivity
from bluebottle.utils.documents import MultiTenantIndex
from bluebottle.utils.models import Language

SCORE_MAP = {
    'open': 1,
    'running': 0.7,
    'full': 0.6,
    'succeeded': 0.5,
    'partially_funded': 0.5,
    'refundend': 0.3,
}


# The name of your index
initiative = MultiTenantIndex('initiatives')
# See Elasticsearch Indices API reference for available settings
initiative.settings(
    number_of_shards=1,
    number_of_replicas=0
)


def deduplicate(items):
    return [dict(s) for s in set(frozenset(d.items()) for d in items)]


def get_translated_list(obj, field='name'):
    data = []

    for lang in Language.objects.all():
        obj.set_current_language(lang.full_code)
        data.append(
            {
                'id': obj.pk,
                field: getattr(obj, field),
                'language': lang.full_code
            }
        )
    return data


@registry.register_document
@initiative.document
class InitiativeDocument(Document):
    title_keyword = fields.KeywordField(attr='title')
    title = fields.TextField(fielddata=True)
    story = fields.TextField()

    pitch = fields.TextField()
    status = fields.KeywordField()
    created = fields.DateField()

    image = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'name': fields.KeywordField(),
    })

    owner = fields.KeywordField()

    country = fields.NestedField(
        properties={
            'id': fields.KeywordField(),
            'name': fields.KeywordField(),
            'language': fields.KeywordField(),
        }
    )

    promoter_id = fields.KeywordField()
    reviewer_id = fields.KeywordField()

    theme = fields.NestedField(
        properties={
            'id': fields.KeywordField(),
            'name': fields.KeywordField(),
            'language': fields.KeywordField(),
        }
    )

    categories = fields.NestedField(
        properties={
            'id': fields.KeywordField(),
            'title': fields.KeywordField(),
            'language': fields.KeywordField()
        }
    )

    segments = fields.NestedField(
        properties={
            'id': fields.KeywordField(),
            'type': fields.KeywordField(attr='segment_type.slug'),
            'name': fields.KeywordField(),
            'closed': fields.BooleanField(),
        }
    )

    activities = fields.NestedField(properties={
        'id': fields.LongField(),
        'title': fields.KeywordField(),
        'status': fields.KeywordField(),
        'activity_date': fields.DateField(),
    })

    open_activities_count = fields.IntegerField()
    succeeded_activities_count = fields.IntegerField()

    place = fields.NestedField(properties={
        'province': fields.TextField(),
        'locality': fields.TextField(),
        'street': fields.TextField(),
        'postal_code': fields.TextField(),
    })

    location = fields.NestedField(
        properties={
            'id': fields.KeywordField(),
            'name': fields.KeywordField(),
            'city': fields.TextField(),
        }
    )

    class Django:
        model = Initiative
        related_models = (
            Geolocation,
            Theme,
            Funding,
            PeriodActivity,
            DateActivity,
            Deed
        )

    def get_queryset(self):
        return super(InitiativeDocument, self).get_queryset().select_related(
            'theme', 'place', 'owner', 'promoter', 'reviewer', 'activity_manager',
            'location'
        ).prefetch_related(
            'activities', 'categories', 'activities__segments', 'activities__segments__segment_type'
        )

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, (Theme, Geolocation, Category)):
            return related_instance.initiative_set.all()
        if isinstance(related_instance, Activity):
            return [related_instance.initiative]

    def prepare_image(self, instance):
        if instance.image and instance.image.file:
            return {
                'id': instance.pk,
                'file': instance.image.file.name,
            }

    def prepare_activities(self, instance):
        return [
            {
                'id': activity.pk,
                'title': activity.title,
                'activity_date': activity.activity_date,
                'status': activity.status,
            } for activity in instance.activities.filter(
                status__in=(
                    'succeeded',
                    'open',
                    'partially_funded',
                    'full',
                    'running'
                )
            )
        ]

    def prepare_open_activities_count(self, instance):
        return instance.activities.filter(
            status__in=(
                'open',
                'full',
                'running'
            )
        ).count()

    def prepare_succeeded_activities_count(self, instance):
        return instance.activities.filter(
            status__in=(
                'succeeded',
                'partially_funded',
            )
        ).count()

    def prepare_owner(self, instance):
        owners = [instance.owner.pk]

        for manager in instance.activity_managers.all():
            owners.append(manager.pk)
        if instance.promoter:
            owners.append(instance.promoter.pk)

        return list(set(owners))

    def prepare_country(self, instance):
        countries = []

        if instance.place and instance.place.country:
            countries += get_translated_list(instance.place.country)

        for activity in instance.activities.filter(
                status__in=['open', 'succeeded', 'full', 'partially_funded']
        ):
            if activity.office_location and activity.office_location.country:
                countries += get_translated_list(activity.office_location.country)

            elif hasattr(activity, 'place') and instance.place and activity.place.country:
                countries += get_translated_list(activity.place.country)

        return deduplicate(countries)

    def prepare_theme(self, instance):
        if hasattr(instance, 'theme') and instance.theme:
            return get_translated_list(instance.theme)

    def prepare_categories(self, instance):
        categories = []
        for category in instance.categories.all():
            categories += get_translated_list(category, 'title')
        return categories

    def prepare_segments(self, instance):
        segments = []

        for activity in instance.activities.all():
            segments += [
                {
                    'id': segment.pk,
                    'type': segment.segment_type.slug,
                    'name': segment.name,
                    'closed': segment.closed,
                }
                for segment in activity.segments.all()
            ]

        return deduplicate(segments)

    def prepare_location(self, instance):
        return deduplicate(
            [
                {
                    'id': activity.office_location.id,
                    'name': activity.office_location.name,
                    'city': activity.office_location.city
                }
                for activity in instance.activities.all() if activity.office_location
            ]
        )
