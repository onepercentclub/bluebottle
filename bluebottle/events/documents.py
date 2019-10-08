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

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Initiative):
            return Event.objects.filter(initiative=related_instance)
        if isinstance(related_instance, Member):
            return Event.objects.filter(owner=related_instance)
        if isinstance(related_instance, Participant):
            return Event.objects.filter(contributions=related_instance)

    def prepare_status_score(self, instance):
        return SCORE_MAP.get(instance.status, 0)

    def prepare_date(self, instance):
        return instance.start_date
