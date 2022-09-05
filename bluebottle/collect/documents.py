from django_elasticsearch_dsl.registries import registry

from bluebottle.activities.documents import ActivityDocument, activity
from bluebottle.collect.models import CollectContributor, CollectActivity
from bluebottle.initiatives.models import Initiative
from bluebottle.members.models import Member

SCORE_MAP = {
    'open': 1,
    'running': 1,
    'succeeded': 0.5,
}


@registry.register_document
@activity.doc_type
class CollectDocument(ActivityDocument):

    def prepare_status_score(self, instance):
        return SCORE_MAP.get(instance.status, 0)

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Initiative):
            return CollectActivity.objects.filter(initiative=related_instance)
        if isinstance(related_instance, Member):
            return CollectActivity.objects.filter(owner=related_instance)
        if isinstance(related_instance, CollectContributor):
            return CollectActivity.objects.filter(contributors=related_instance)

    class Django:
        related_models = (Initiative, Member, CollectContributor)
        model = CollectActivity

    def prepare_start(self, instance):
        return instance.start

    def prepare_end(self, instance):
        return [instance.end]

    def prepare_duration(self, instance):
        if instance.start and instance.end and instance.start > instance.end:
            return {}
        return {'gte': instance.start, 'lte': instance.end}
