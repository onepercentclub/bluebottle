from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from bluebottle.organizations.models import Organization
from bluebottle.activities.models import Activity
from bluebottle.initiatives.models import Initiative
from bluebottle.collect.models import CollectActivity
from bluebottle.deeds.models import Deed
from bluebottle.funding.models import Funding
from bluebottle.grant_management.models import GrantApplication
from bluebottle.time_based.models import (
    DateActivity, DeadlineActivity, PeriodicActivity, RegisteredDateActivity, ScheduleActivity
)
from bluebottle.utils.documents import MultiTenantIndex, TextField

# The name of your index
organization = MultiTenantIndex('organizations')
# See Elasticsearch Indices API reference for available settings
organization.settings(
    number_of_shards=1,
    number_of_replicas=0
)


@registry.register_document
@organization.document
class OrganizationsDocument(Document):
    name_keyword = fields.KeywordField(attr='name')
    name = TextField(fielddata=True)
    slug = fields.KeywordField()

    story = TextField(attr='story.html')
    slogan = TextField()
    website = TextField()

    created = fields.DateField()

    image = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'name': fields.KeywordField(),
    })

    logo = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'name': fields.KeywordField(),
    })

    open_activities_count = fields.IntegerField()
    succeeded_activities_count = fields.IntegerField()

    class Django:
        model = Organization
        # Signals are matched on the exact model class, so list the concrete
        # (polymorphic) activity types instead of the Activity base class.
        related_models = (
            Initiative,
            DateActivity,
            DeadlineActivity,
            PeriodicActivity,
            ScheduleActivity,
            RegisteredDateActivity,
            Funding,
            GrantApplication,
            CollectActivity,
            Deed,
        )

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, (Initiative, Activity)) and related_instance.organization:
            yield related_instance.organization

    def prepare_image(self, instance):
        return {
            'id': instance.pk,
            'file': instance.image.name,
        }

    def prepare_logo(self, instance):
        return {
            'id': instance.pk,
            'file': instance.logo.name,
        }

    def prepare_open_activities_count(self, instance):
        return instance.activities.filter(
            status__in=(
                'open',
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
