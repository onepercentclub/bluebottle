from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from bluebottle.time_based.models import PeriodActivity, DateActivity
from bluebottle.utils.documents import MultiTenantIndex

from bluebottle.initiatives.models import Initiative, Theme
from bluebottle.geo.models import Geolocation
from bluebottle.categories.models import Category
from bluebottle.activities.models import Activity
from bluebottle.funding.models import Funding
from bluebottle.deeds.models import Deed
from bluebottle.members.models import Member


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


@registry.register_document
@initiative.document
class InitiativeDocument(Document):
    title_keyword = fields.KeywordField(attr='title')
    title = fields.TextField(fielddata=True)
    story = fields.TextField()
    pitch = fields.TextField()
    status = fields.KeywordField()
    created = fields.DateField()

    owner = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'full_name': fields.TextField()
    })
    promoter = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'full_name': fields.TextField()
    })
    activity_managers = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'full_name': fields.TextField()
    })
    activity_owners = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'full_name': fields.TextField()
    })

    country = fields.LongField()
    owner_id = fields.KeywordField()
    promoter_id = fields.KeywordField()
    reviewer_id = fields.KeywordField()

    theme = fields.NestedField(properties={
        'id': fields.KeywordField(),
    })
    categories = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'slug': fields.KeywordField(),
    })

    segments = fields.NestedField(
        properties={
            'id': fields.KeywordField(),
            'segment_type': fields.KeywordField(attr='segment_type.slug'),
            'name': fields.TextField()
        }
    )

    activities = fields.NestedField(properties={
        'id': fields.LongField(),
        'title': fields.KeywordField(),
        'activity_date': fields.DateField(),
        'status_score': fields.FloatField()
    })

    place = fields.NestedField(properties={
        'province': fields.TextField(),
        'locality': fields.TextField(),
        'street': fields.TextField(),
        'postal_code': fields.TextField(),
    })

    location = fields.NestedField(
        properties={
            'id': fields.LongField(),
            'name': fields.TextField(),
            'city': fields.TextField(),
        }
    )

    class Django:
        model = Initiative
        related_models = (
            Geolocation,
            Member,
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
        if isinstance(related_instance, Member):
            return list(related_instance.own_initiatives.all()) + list(related_instance.review_initiatives.all())
        if isinstance(related_instance, Activity):
            return [related_instance.initiative]

    def prepare_activities(self, instance):
        return [
            {
                'id': activity.pk,
                'title': activity.title,
                'activity_date': activity.activity_date,
                'status_score': SCORE_MAP[activity.status],
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

    def prepare_segments(self, instance):
        segments = []

        for activity in instance.activities.all():
            segments += [
                {
                    'id': segment.id,
                    'name': segment.name,
                    'segment_type': segment.segment_type.slug
                }
                for segment in activity.segments.all()
            ]

        return segments

    def prepare_location(self, instance):
        return [{
            'id': activity.office_location.id,
            'name': activity.office_location.name,
            'city': activity.office_location.city
        } for activity in instance.activities.all() if activity.office_location]

    def prepare_activity_owners(self, instance):
        return [
            {
                'id': activity.owner.pk,
                'full_name': activity.owner.full_name
            } for activity in instance.activities.all()
        ]

    def prepare_country(self, instance):
        countries = []
        if instance.place and instance.place.country_id:
            countries += [instance.place.country_id]
        if instance.location and instance.location.country_id:
            countries += [instance.location.country_id]
        return countries
