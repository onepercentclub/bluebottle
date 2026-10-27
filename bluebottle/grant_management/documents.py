from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry

from bluebottle.activities.documents import ActivityDocument, activity
from bluebottle.grant_management.models import GrantApplication


@registry.register_document
@activity.doc_type
class GrantApplicationDocument(ActivityDocument):
    target = fields.NestedField(properties={
        'currency': fields.KeywordField(),
        'amount': fields.FloatField(),
    })

    class Django:
        model = GrantApplication

    def prepare_dates(self, instance):
        return [{
            'start': instance.created,
            'end': instance.created
        }]

    def prepare_target(self, instance):
        if instance.target:
            return {
                'amount': instance.target.amount,
                'currency': str(instance.target.currency)
            }

    def prepare_is_online(self, instance):
        return True
