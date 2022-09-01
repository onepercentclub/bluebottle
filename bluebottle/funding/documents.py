from django_elasticsearch_dsl.registries import registry
from django_elasticsearch_dsl import fields

from bluebottle.activities.documents import ActivityDocument, activity
from bluebottle.funding.models import Funding, Donor
from bluebottle.initiatives.models import Initiative
from bluebottle.members.models import Member

SCORE_MAP = {
    'open': 1,
    'succeeded': 0.5,
    'partially_funded': 0.5,
    'refundend': 0.3,
}


@registry.register_document
@activity.doc_type
class FundingDocument(ActivityDocument):
    target = fields.NestedField(properties={
        'currency': fields.KeywordField(),
        'amount': fields.FloatField(),
    })
    amount_raised = fields.NestedField(properties={
        'currency': fields.KeywordField(),
        'amount': fields.FloatField(),
    })

    class Django:
        model = Funding
        related_models = (Initiative, Member, Donor)

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Initiative):
            return Funding.objects.filter(initiative=related_instance)
        if isinstance(related_instance, Member):
            return Funding.objects.filter(owner=related_instance)
        if isinstance(related_instance, Donor):
            return Funding.objects.filter(contributors=related_instance)

    def prepare_status_score(self, instance):
        return SCORE_MAP.get(instance.status, 0)

    def prepare_end(self, instance):
        return instance.deadline

    def prepare_duration(self, instance):
        if instance.started and instance.deadline and instance.started > instance.deadline:
            return {}
        return {'gte': instance.started, 'lte': instance.deadline}

    def prepare_amount(self, amount):
        if amount:
            return {'amount': amount.amount, 'currency': str(amount.currency)}

    def prepare_target(self, instance):
        return self.prepare_amount(instance.target)

    def prepare_amount_raised(self, instance):
        return self.prepare_amount(instance.amount_raised)
