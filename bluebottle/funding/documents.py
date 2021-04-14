from django_elasticsearch_dsl.registries import registry

from bluebottle.activities.documents import ActivityDocument, activity
from bluebottle.funding.models import Funding, Donor
from bluebottle.initiatives.models import Initiative
from bluebottle.members.models import Member

SCORE_MAP = {
    'open': 1,
    'succeeded': 0.5,
    'partially_funded': 0.4,
    'refundend': 0.3,
}


@registry.register_document
@activity.doc_type
class FundingDocument(ActivityDocument):
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
