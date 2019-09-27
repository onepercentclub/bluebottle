from bluebottle.activities.documents import ActivityDocument, activity
from bluebottle.assignments.models import Assignment
from bluebottle.funding.models import Contribution
from bluebottle.initiatives.models import Initiative
from bluebottle.members.models import Member


@activity.doc_type
class AssignmentDocument(ActivityDocument):
    class Meta:
        model = Assignment
        related_models = (Initiative, Member, Contribution)
