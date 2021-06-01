from bluebottle.activities.documents import ActivityDocument, activity
from bluebottle.initiatives.models import Initiative
from bluebottle.members.models import Member
from bluebottle.time_based.models import (
    DateActivity, PeriodActivity, DateParticipant, PeriodParticipant, DateActivitySlot
)

SCORE_MAP = {
    'open': 1,
    'running': 0.7,
    'full': 0.6,
    'succeeded': 0.5,
}


class TimeBasedActivityDocument:

    def prepare_status_score(self, instance):
        return SCORE_MAP.get(instance.status, 0)


@activity.doc_type
class DateActivityDocument(TimeBasedActivityDocument, ActivityDocument):
    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Initiative):
            return DateActivity.objects.filter(initiative=related_instance)
        if isinstance(related_instance, Member):
            return DateActivity.objects.filter(owner=related_instance)
        if isinstance(related_instance, DateParticipant):
            return DateActivity.objects.filter(contributors=related_instance)
        if isinstance(related_instance, DateActivitySlot):
            return related_instance.activity

    class Meta(object):
        related_models = (Initiative, Member, DateParticipant, DateActivitySlot)
        model = DateActivity

    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            'slots'
        )

    def prepare_location(self, instance):
        return [
            {'id': slot.location.id, 'formatted_address': slot.location.formatted_address}
            for slot in instance.slots.all()
            if not slot.is_online and slot.location
        ]

    def prepare_start(self, instance):
        return [slot.start for slot in instance.slots.all()]

    def prepare_end(self, instance):
        return [
            slot.start + slot.duration
            for slot in instance.slots.all()
            if slot.start and slot.duration
        ]

    def prepare_country(self, instance):
        return [
            slot.location.country_id for slot in instance.slots.all()
            if not slot.is_online and slot.location
        ]

    def prepare_position(self, instance):
        return [
            {'lat': slot.location.position.get_y(), 'lon': slot.location.position.get_x()}
            for slot in instance.slots.all()
            if not slot.is_online and slot.location
        ]

    def prepare_is_online(self, instance):
        return any(slot.is_online for slot in instance.slots.all())


@ activity.doc_type
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

    def prepare_country(self, instance):
        if not instance.is_online and instance.location:
            return instance.location.country_id
        else:
            return super().prepare_country(instance)

    def prepare_position(self, instance):
        if not instance.is_online and instance.location:
            position = instance.location.position
            return {'lat': position.get_y(), 'lon': position.get_x()}

    def prepare_end(self, instance):
        return instance.deadline
