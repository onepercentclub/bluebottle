from bluebottle.activities.documents import ActivityDocument, activity
from bluebottle.funding.models import Funding, Contribution
from bluebottle.initiatives.models import Initiative
from bluebottle.members.models import Member


@activity.doc_type
class FundingDocument(ActivityDocument):
    class Meta:
        model = Funding
        related_models = (Initiative, Member, Contribution)
