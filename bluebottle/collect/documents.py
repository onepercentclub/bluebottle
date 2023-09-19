from datetime import datetime
from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry

from bluebottle.activities.documents import ActivityDocument, activity
from bluebottle.collect.models import CollectContributor, CollectActivity, CollectType

SCORE_MAP = {
    'open': 1,
    'running': 1,
    'succeeded': 0.5,
}


@registry.register_document
@activity.doc_type
class CollectDocument(ActivityDocument):
    collect_type = fields.NestedField(
        attr='initiative.theme',
        properties={
            'id': fields.KeywordField(),
            'name': fields.KeywordField(),
        }
    )

    def prepare_status_score(self, instance):
        return SCORE_MAP.get(instance.status, 0)

    def get_instances_from_related(self, related_instance):
        result = super().get_instances_from_related(related_instance)
        if result is not None:
            return result

        if isinstance(related_instance, CollectContributor):
            return CollectActivity.objects.filter(contributors=related_instance)

        if isinstance(related_instance, CollectType):
            return CollectActivity.objects.filter(collect_type=related_instance)

        if isinstance(related_instance, CollectType.translations.field.model):
            return CollectActivity.objects.filter(collect_type=related_instance.master)

    class Django:
        related_models = ActivityDocument.Django.related_models + (
            CollectContributor, CollectType, CollectType.translations.field.model
        )
        model = CollectActivity

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

    def prepare_collect_type(self, instance):
        if not instance.collect_type:
            return []
        return [
            {'name': translation.name, 'language': translation.language_code}
            for translation in instance.collect_type.translations.all()
        ]

    def prepare_position(self, instance):
        if instance.location:
            position = instance.location.position
            return [{'lat': position.y, 'lon': position.x}]

    def prepare_is_online(self, instance):
        return not instance.location
