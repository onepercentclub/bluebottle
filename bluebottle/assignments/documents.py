from bluebottle.activities.documents import ActivityDocument, activity
from bluebottle.assignments.models import Assignment
from bluebottle.funding.models import Contribution
from bluebottle.initiatives.models import Initiative
from bluebottle.members.models import Member

SCORE_MAP = {
    'open': 1,
    'running': 0.7,
    'full': 0.6,
    'succeeded': 0.5,
}


@activity.doc_type
class AssignmentDocument(ActivityDocument):
    class Meta:
        model = Assignment
        related_models = (Initiative, Member, Contribution)

    def prepare_status_score(self, instance):
        return SCORE_MAP.get(instance.status, 0)
