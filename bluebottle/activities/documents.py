from builtins import str
from builtins import object
from django_elasticsearch_dsl import DocType, fields

from bluebottle.utils.documents import MultiTenantIndex
from bluebottle.activities.models import Activity
from bluebottle.utils.search import Search


# The name of your index
activity = MultiTenantIndex('activity')
# See Elasticsearch Indices API reference for available settings
activity.settings(
    number_of_shards=1,
    number_of_replicas=0
)


class ActivityDocument(DocType):
    title_keyword = fields.KeywordField(attr='title')
    title = fields.TextField(fielddata=True)
    description = fields.TextField()
    status = fields.KeywordField()
    status_score = fields.FloatField()
    created = fields.DateField()

    type = fields.KeywordField()

    owner = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'full_name': fields.TextField()
    })

    initiative = fields.NestedField(properties={
        'title': fields.TextField(),
        'pitch': fields.TextField(),
        'story': fields.TextField(),
    })

    theme = fields.NestedField(
        attr='initiative.theme',
        properties={
            'id': fields.KeywordField(),
        }
    )

    categories = fields.NestedField(
        attr='initiative.categories',
        properties={
            'id': fields.LongField(),
            'slug': fields.KeywordField(),
        }
    )
    position = fields.GeoPointField()

    country = fields.KeywordField()

    expertise = fields.NestedField(
        properties={
            'id': fields.KeywordField(),
        }
    )

    segments = fields.NestedField(
        properties={
            'id': fields.KeywordField(),
            'type': fields.KeywordField(attr='type.slug'),
            'name': fields.TextField()
        }
    )

    location = fields.NestedField(
        attr='location',
        properties={
            'id': fields.LongField(),
            'formatted_address': fields.TextField(),
        }
    )

    initiative_location = fields.NestedField(
        attr='initiative.location',
        properties={
            'id': fields.LongField(),
            'name': fields.TextField(),
            'city': fields.TextField(),
        }
    )

    contributors = fields.DateField()
    contributor_count = fields.IntegerField()

    start = fields.DateField()
    end = fields.DateField()
    activity_date = fields.DateField()

    class Meta(object):
        model = Activity

    date_field = None

    def get_queryset(self):
        return super(ActivityDocument, self).get_queryset().select_related(
            'initiative', 'owner',
        )

    @classmethod
    def search(cls, using=None, index=None):
        # Use search class that supports polymorphic models
        return Search(
            using=using or cls._doc_type.using,
            index=index or cls._doc_type.index,
            doc_type=[cls],
            model=cls._doc_type.model
        )

    def prepare_contributors(self, instance):
        return [
            contributor.created for contributor
            in instance.contributors.filter(status__in=('new', 'success', 'accepted'))
        ]

    def prepare_type(self, instance):
        return str(instance.__class__.__name__.lower())

    def prepare_contributor_count(self, instance):
        return instance.contributors.filter(status__in=('new', 'success', 'accepted')).count()

    def prepare_country(self, instance):
        if instance.initiative.location:
            return instance.initiative.location.country_id
        if instance.initiative.place:
            return instance.initiative.place.country_id

    def prepare_location(self, instance):
        if hasattr(instance, 'location') and instance.location:
            return {
                'id': instance.location.pk,
                'formatted_address': instance.location.formatted_address
            }

    def prepare_expertise(self, instance):
        if hasattr(instance, 'expertise') and instance.expertise:
            return {'id': instance.expertise_id}

    def prepare_position(self, instance):
        return None

    def prepare_end(self, instance):
        return None

    def prepare_start(self, instance):
        return None
