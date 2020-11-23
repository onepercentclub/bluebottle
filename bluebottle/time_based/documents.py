from bluebottle.activities.documents import ActivityDocument, activity

from bluebottle.initiatives.models import Initiative
from bluebottle.members.models import Member
from bluebottle.time_based.models import DateActivity, PeriodActivity, DateParticipant, PeriodParticipant

SCORE_MAP = {
    'open': 1,
    'running': 0.7,
    'full': 0.6,
    'succeeded': 0.5,
}


class TimeBasedActivityDocument:

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
class DateActivityDocument(TimeBasedActivityDocument, ActivityDocument):
    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Initiative):
            return DateActivity.objects.filter(initiative=related_instance)
        if isinstance(related_instance, Member):
            return DateActivity.objects.filter(owner=related_instance)
        if isinstance(related_instance, DateParticipant):
            return DateActivity.objects.filter(contributors=related_instance)

    class Meta(object):
        related_models = (Initiative, Member, DateParticipant)
        model = DateActivity

    def prepare_start(self, instance):
        return instance.start

    def prepare_end(self, instance):
        if instance.start and instance.duration:
            return instance.start + instance.duration
        return None


@activity.doc_type
class PeriodActivityDocument(TimeBasedActivityDocument, ActivityDocument):
    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Initiative):
            return PeriodActivity.objects.filter(initiative=related_instance)
        if isinstance(related_instance, Member):
            return PeriodActivity.objects.filter(owner=related_instance)
        if isinstance(related_instance, PeriodParticipant):
            return PeriodActivity.objects.filter(contributors=related_instance)

    class Meta(object):
        related_models = (Initiative, Member, PeriodParticipant)
        model = PeriodActivity

    def prepare_end(self, instance):
        return instance.deadline
