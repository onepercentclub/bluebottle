from datetime import datetime
from django_elasticsearch_dsl.registries import registry

from bluebottle.activities.documents import ActivityDocument, activity
from bluebottle.deeds.models import DeedParticipant, Deed

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
        result = super().get_instances_from_related(related_instance)

        if result is not None:
            return result

        if isinstance(related_instance, DeedParticipant):
            return Deed.objects.filter(contributors=related_instance)

    class Django:
        related_models = ActivityDocument.Django.related_models + (DeedParticipant, )
        model = Deed

    def prepare_start(self, instance):
        return [instance.start]

    def prepare_end(self, instance):
        return [instance.end]

    def prepare_dates(self, instance):
        return [{
            'start': instance.start or datetime.min,
            'end': instance.end or datetime.max
        }]

    def prepare_duration(self, instance):
        if instance.start and instance.end and instance.start > instance.end:
            return {}
        return {'gte': instance.start, 'lte': instance.end}
