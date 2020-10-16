import datetime

from bluebottle.activities.documents import ActivityDocument, activity

from bluebottle.time_based.models import OnADateActivity, WithADeadlineActivity, OngoingActivity
from bluebottle.initiatives.models import Initiative
from bluebottle.members.models import Member

SCORE_MAP = {
    'open': 1,
    'running': 0.7,
    'full': 0.6,
    'succeeded': 0.5,
}


class TimeBasedActivityDocument:
    class Meta:
        related_models = (Initiative, Member)

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Initiative):
            return self.Meta.model.objects.filter(initiative=related_instance)
        if isinstance(related_instance, Member):
            return self.Meta.model.objects.filter(owner=related_instance)

    def prepare_status_score(self, instance):
        return SCORE_MAP.get(instance.status, 0)

    def prepare_country(self, instance):
        if not instance.is_online and instance.location:
            return instance.location.country_id
        else:
            return super().prepare_country(instance)

    def prepare_position(self, instance):
        if not instance.is_online and instance.location:
            position = instance.location.position
            return {'lat': position.get_y(), 'lon': position.get_x()}


@activity.doc_type
class OnADateActivityDocument(TimeBasedActivityDocument, ActivityDocument):
    class Meta(TimeBasedActivityDocument):
        model = OnADateActivity

    def prepare_start(self, instance):
        return instance.start

    def prepare_end(self, instance):
        if instance.start and instance.duration:
            return instance.start + datetime.timedelta(hours=instance.duration)


@activity.doc_type
class WithADeadlineActivityDocument(TimeBasedActivityDocument, ActivityDocument):
    class Meta(TimeBasedActivityDocument):
        model = WithADeadlineActivity

    def prepare_end(self, instance):
        return instance.deadline


@activity.doc_type
class OngoingActivityDocument(TimeBasedActivityDocument, ActivityDocument):
    class Meta(TimeBasedActivityDocument):
        model = OngoingActivity
