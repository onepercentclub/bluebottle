from django_elasticsearch_dsl.registries import registry

from bluebottle.activities.documents import ActivityDocument, activity
from bluebottle.deeds.models import DeedParticipant, Deed
from bluebottle.initiatives.models import Initiative
from bluebottle.members.models import Member

SCORE_MAP = {
    'open': 1,
    'running': 1,
    'succeeded': 0.5,
}


@registry.register_document
@activity.doc_type
class DeedDocument(ActivityDocument):

    def prepare_status_score(self, instance):
        return SCORE_MAP.get(instance.status, 0)

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Initiative):
            return Deed.objects.filter(initiative=related_instance)
        if isinstance(related_instance, Member):
            return Deed.objects.filter(owner=related_instance)
        if isinstance(related_instance, DeedParticipant):
            return Deed.objects.filter(contributors=related_instance)

    class Django:
        related_models = (Initiative, Member, DeedParticipant)
        model = Deed

    def prepare_start(self, instance):
        return instance.start

    def prepare_end(self, instance):
        return instance.end
