from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry

from bluebottle.activities.documents import ActivityDocument, activity
from bluebottle.grant_management.models import GrantApplication, GrantDonor


@registry.register_document
@activity.doc_type
class GrantApplicationDocument(ActivityDocument):
    target = fields.NestedField(properties={
        'currency': fields.KeywordField(),
        'amount': fields.FloatField(),
    })

    class Django:
        model = GrantApplication

    def get_sort_date(self, instance):
        if instance.started:
            return instance.started

        grant = (
            instance.contributors.instance_of(GrantDonor)
            .order_by('created')
            .first()
        )
        if grant:
            return grant.created

        return instance.created

    def prepare_dates(self, instance):
        sort_date = self.get_sort_date(instance)
        return [{
            'start': sort_date,
            'end': sort_date,
        }]

    def prepare_start(self, instance):
        return [self.get_sort_date(instance)]

    def prepare_end(self, instance):
        return [self.get_sort_date(instance)]

    def prepare_target(self, instance):
        if instance.target:
            return {
                'amount': instance.target.amount,
                'currency': str(instance.target.currency)
            }

    def prepare_is_online(self, instance):
        return True
