from django.db import connection

from django_elasticsearch_dsl import Index, DocType, fields, search
from elasticsearch_dsl import Q

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.categories.models import Category
from bluebottle.donations.models import Donation
from bluebottle.geo.models import Location, Country
from bluebottle.projects.models import Project, ProjectLocation
from bluebottle.tasks.models import Task, TaskMember
from bluebottle.votes.models import Vote

# The name of your index
project = Index('projects')
# See Elasticsearch Indices API reference for available settings
project.settings(
    number_of_shards=1,
    number_of_replicas=0
)


@project.doc_type
class ProjectDocument(DocType):
    client_name = fields.KeywordField()
    title = fields.TextField()
    story = fields.TextField()
    pitch = fields.TextField()
    owner_id = fields.KeywordField()

    task_set = fields.NestedField(properties={
        'title': fields.TextField(),
        'description': fields.TextField(),
        'type': fields.KeywordField(),
        'status': fields.TextField(),
        'deadline': fields.DateField(),
        'deadline_to_apply': fields.DateField(),
        'location': fields.TextField(),
        'location_keyword': fields.KeywordField(attr='location'),
        'skill': fields.ObjectField(
            properties={
                'id': fields.LongField(),
            }
        ),
    })

    task_members = fields.DateField()
    donations = fields.DateField()
    votes = fields.DateField()

    status = fields.ObjectField(properties={
        'slug': fields.KeywordField(),
        'sequence': fields.ShortField(),
        'viewable': fields.BooleanField()
    })

    position = fields.GeoPointField()

    location = fields.NestedField(properties={
        'id': fields.LongField(),
        'position': fields.GeoPointField(attr='position_tuple'),
        'city': fields.TextField(),
        'name': fields.TextField()
    })

    country = fields.ObjectField(properties={
        'id': fields.LongField(),
    })

    theme = fields.ObjectField(properties={
        'id': fields.LongField(),
    })

    categories = fields.NestedField(properties={
        'id': fields.LongField(),
    })

    amount_asked = fields.FloatField()
    amount_needed = fields.FloatField()

    deadline = fields.DateField()
    created = fields.DateField()
    campaign_started = fields.DateField()

    class Meta:
        model = Project
        related_models = (
            Task, TaskMember, ProjectPhase, Location, Country, Vote, Donation,
        )

    @classmethod
    def search(cls, using=None, index=None):
        return search.Search(
            using=using or cls._doc_type.using,
            index=index or cls._doc_type.index,
            doc_type=[cls],
            model=cls._doc_type.model
        ).filter(Q('term', client_name=connection.tenant.client_name))

    def get_queryset(self):
        return super(ProjectDocument, self).get_queryset().select_related(
            'location', 'country', 'theme', 'status'
        )

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Task):
            return related_instance.project
        if isinstance(related_instance, TaskMember):
            return related_instance.task.project
        elif isinstance(related_instance, ProjectPhase):
            return related_instance.project_set.all()
        elif isinstance(related_instance, Location):
            return related_instance.project_set.all()
        elif isinstance(related_instance, Country):
            return related_instance.project_set.all()
        elif isinstance(related_instance, Category):
            return related_instance.project_set.all()
        elif isinstance(related_instance, Vote):
            return related_instance.project
        elif isinstance(related_instance, Donation):
            return related_instance.project

    def prepare_client_name(self, instance):
        return connection.tenant.client_name

    def prepare_amount_asked(self, instance):
        return instance.amount_asked.amount

    def prepare_amount_needed(self, instance):
        return instance.amount_needed.amount

    def prepare_votes(self, instance):
        return [vote.created for vote in instance.vote_set.all()]

    def prepare_donations(self, instance):
        return [donation.created for donation in instance.donation_set.all()]

    def prepare_position(self, instance):
        try:
            return instance.projectlocation.position
        except ProjectLocation.DoesNotExist:
            return None

    def prepare_task_members(self, instance):
        result = []
        for task in instance.task_set.all():
            result += [
                member.created for member in task.members.all()
            ]

        return result
