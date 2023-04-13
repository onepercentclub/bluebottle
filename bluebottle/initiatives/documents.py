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

    image = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'name': fields.KeywordField(),
    })

    owner = fields.KeywordField()

    country = fields.NestedField(
        properties={
            'id': fields.KeywordField(),
            'name': fields.KeywordField(),
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

    def prepare_image(self, instance):
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

    def prepare_owner(self, instance):
        owners = [instance.owner.pk]

        for manager in instance.activity_managers.all():
            owners.append(manager.pk)
        if instance.promoter:
            owners.append(instance.owner.promoter)

        return owners

    def prepare_country(self, instance):
        countries = []

        for activity in instance.activities.filter(
                status__in=['open', 'succeeded', 'full', 'partially_funded']
        ):
            if activity.office_location:
                countries.append({
                    'id': activity.office_location.country.pk,
                    'name': activity.office_location.country.name,
                })
            elif hasattr(activity, 'place') and instance.place:
                countries.append({
                    'id': activity.place.country.pk,
                    'name': activity.place.country.name,
                })

        return countries

    def prepare_theme(self, instance):
        if hasattr(instance, 'theme') and instance.theme:
            return [
                {
                    'id': instance.theme_id,
                    'name': translation.name,
                    'language': translation.language_code,
                }
                for translation in instance.theme.translations.all()
            ]

    def prepare_categories(self, instance):
        return [
            {
                'id': category.pk,
                'title': translation.title,
                'language': translation.language_code,
            }
            for category in instance.categories.all()
            for translation in category.translations.all()
        ]

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

        return segments

    def prepare_location(self, instance):
        return [{
            'id': activity.office_location.id,
            'name': activity.office_location.name,
            'city': activity.office_location.city
        } for activity in instance.activities.all() if activity.office_location]
