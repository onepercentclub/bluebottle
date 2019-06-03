from bluebottle.activities.documents import ActivityDocument, activity
from bluebottle.events.models import Event
from bluebottle.initiatives.models import Initiative
from bluebottle.members.models import Member


@activity.doc_type
class EventDocument(ActivityDocument):
    class Meta:
        model = Event
        related_models = (Initiative, Member)
