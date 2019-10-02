from bluebottle.activities.documents import ActivityDocument, activity
from bluebottle.funding.models import Funding, Contribution
from bluebottle.initiatives.models import Initiative
from bluebottle.members.models import Member

SCORE_MAP = {
    'open': 1,
    'succeeded': 0.5,
    'partially_funded': 0.4,
    'refundend': 0.3,
}


@activity.doc_type
class FundingDocument(ActivityDocument):
    class Meta:
        model = Funding
        related_models = (Initiative, Member, Contribution)

    def prepare_status_score(self, instance):
        return SCORE_MAP.get(instance.status, 0)
