from django_elasticsearch_dsl import DocType, fields

from bluebottle.utils.documents import MultiTenantIndex

from bluebottle.initiatives.models import Initiative
from bluebottle.activities.models import Activity, Contribution
from bluebottle.members.models import Member
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
        attr='initiative.theme',
        properties={
            'id': fields.LongField(),
            'slug': fields.KeywordField(),
        }
    )

    country = fields.KeywordField()

    expertise = fields.NestedField(
        attr='expertise',
        properties={
            'id': fields.KeywordField(),
        }
    )

    contributions = fields.DateField()
    contribution_count = fields.IntegerField()

    class Meta:
        model = Activity
        related_models = (Initiative, Member, Contribution)

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

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Initiative):
            return related_instance.activities.all()
        if isinstance(related_instance, Member):
            return related_instance.activities.all()
        if isinstance(related_instance, Contribution):
            return related_instance.activity

    def prepare_contributions(self, instance):
        return [
            contribution.created for contribution
            in instance.contributions.filter(status__in=('new', 'success'))
        ]

    def prepare_type(self, instance):
        return unicode(instance.__class__.__name__.lower())

    def prepare_contribution_count(self, instance):
        return len(instance.contributions.filter(status__in=('new', 'success')))

    def prepare_country(self, instance):
        if hasattr(instance, 'location') and instance.location:
            return instance.location.country_id

    def prepare_expertise(self, instance):
        if hasattr(instance, 'expertise') and instance.expertise:
            return {'id': instance.expertise_id}
