from django_elasticsearch_dsl import DocType, fields

from bluebottle.utils.documents import MultiTenantIndex

from bluebottle.initiatives.models import Initiative
from bluebottle.bb_projects.models import ProjectTheme
from bluebottle.geo.models import InitiativePlace
from bluebottle.categories.models import Category
from bluebottle.members.models import Member


# The name of your index
initiative = MultiTenantIndex('initiatives')
# See Elasticsearch Indices API reference for available settings
initiative.settings(
    number_of_shards=1,
    number_of_replicas=0
)


@initiative.doc_type
class InitiativeDocument(DocType):
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

    owner_id = fields.KeywordField()
    promoter_id = fields.KeywordField()
    reviewer_id = fields.KeywordField()
    theme = fields.NestedField(properties={
        'id': fields.KeywordField(),
    })
    categories = fields.NestedField(properties={
        'id': fields.LongField(),
    })

    place = fields.NestedField(properties={
        'country': fields.LongField(attr='country.pk'),
        'province': fields.LongField(),
        'locality': fields.TextField(),
        'street': fields.TextField(),
        'postal_code': fields.TextField(),
    })

    class Meta:
        model = Initiative
        related_models = (
            InitiativePlace, Member, ProjectTheme
        )

    def get_queryset(self):
        return super(InitiativeDocument, self).get_queryset().select_related(
            'theme', 'place', 'owner', 'promoter',
        )

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, (ProjectTheme, InitiativePlace, Category)):
            return related_instance.initiative_set.all()
        if isinstance(related_instance, Member):
            return list(related_instance.own_initiatives.all()) + list(related_instance.review_initiatives.all())
