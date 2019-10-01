from bluebottle.activities.documents import ActivityDocument, activity
from bluebottle.events.models import Event, Participant
from bluebottle.initiatives.models import Initiative
from bluebottle.members.models import Member

SCORE_MAP = {
    'open': 1,
    'running': 0.7,
    'full': 0.6,
    'succeeded': 0.5,
}


@activity.doc_type
class EventDocument(ActivityDocument):
    class Meta:
        model = Event
        related_models = (Initiative, Member, Participant)

    def prepare_status_score(self, instance):
        return SCORE_MAP.get(instance.status, 0)
