from django.db import connection

from django_elasticsearch_dsl import Index, DocType, fields, search

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.categories.models import Category
from bluebottle.donations.models import Donation
from bluebottle.geo.models import Location, Country
from bluebottle.projects.models import Project
from bluebottle.tasks.models import Task

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

    task_set = fields.NestedField(properties={
        'title': fields.StringField(),
        'description': fields.StringField(),
        'type': fields.KeywordField(),
        'status': fields.StringField(),
        'deadline': fields.DateField(),
        'deadline_to_apply': fields.DateField(),
        'location': fields.StringField(),
        'skill': fields.ObjectField(
            properties={
                'id': fields.LongField(),
                'name': fields.KeywordField()
            }
        ),
    })

    task_member_set = fields.NestedField(properties={
        'created': fields.DateField()
    })

    donation_set = fields.NestedField(properties={
        'created': fields.DateField()
    })

    vote_set = fields.NestedField(properties={
        'created': fields.DateField()
    })

    status = fields.ObjectField(properties={
        'slug': fields.KeywordField()
    })

    location = fields.ObjectField(properties={
        'id': fields.LongField(),
        'name': fields.StringField(),
        'position': fields.GeoPointField(attr='position_tuple'),
        'city': fields.StringField()
    })

    country = fields.ObjectField(properties={
        'id': fields.LongField(),
        'name': fields.StringField(),
    })

    theme = fields.ObjectField(properties={
        'id': fields.LongField(),
        'name': fields.StringField(),
    })

    categories = fields.NestedField(properties={
        'id': fields.LongField(),
        'title': fields.StringField(),
    })

    project_location = fields.GeoPointField()
    amount_asked = fields.FloatField()

    class Meta:
        model = Project
        fields = [
            'title',
            'story',
            'pitch',
            'popularity',
        ]
        related_models = (Task, ProjectPhase, Location, Donation, Country)

    @classmethod
    def search(cls, using=None, index=None):
        return search.Search(
            using=using or cls._doc_type.using,
            index=index or cls._doc_type.index,
            doc_type=[cls],
            model=cls._doc_type.model
        )

    def get_queryset(self):
        return super(ProjectDocument, self).get_queryset().select_related(
            'location', 'country', 'theme', 'status'
        )

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Task):
            return related_instance.project
        elif isinstance(related_instance, ProjectPhase):
            return related_instance.project_set.all()
        elif isinstance(related_instance, Location):
            return related_instance.project_set.all()
        elif isinstance(related_instance, Country):
            return related_instance.project_set.all()
        elif isinstance(related_instance, Category):
            return related_instance.project_set.all()
        elif isinstance(related_instance, Donation):
            return related_instance.project

    def prepare_client_name(self, instance):
        return connection.tenant.client_name

    def prepare_amount_asked(self, instance):
        return instance.amount_asked.amount

    def prepare_project_location(self, instance):
        if instance.latitude and instance.longitude:
            return (instance.longitude, instance.latitude)
        else:
            return None

    def prepare_task_member_set(self, instance):
        result = []
        for task in instance.task_set.all():
            result += [
                {'created': member.created} for member in task.members.all()
            ]

        return result
