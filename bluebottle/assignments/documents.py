from bluebottle.activities.documents import ActivityDocument, activity
from bluebottle.assignments.models import Assignment, Applicant
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
        related_models = (Initiative, Member, Applicant)

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Initiative):
            return Assignment.objects.filter(initiative=related_instance)
        if isinstance(related_instance, Member):
            return Assignment.objects.filter(owner=related_instance)
        if isinstance(related_instance, Applicant):
            return Assignment.objects.filter(contributions=related_instance)

    def prepare_status_score(self, instance):
        return SCORE_MAP.get(instance.status, 0)

    def prepare_deadline(self, instance):
        if instance.end_date_type == 'deadline':
            return instance.end_date

    def prepare_date(self, instance):
        if instance.end_date_type == 'on_date':
            return instance.end_date

    def prepare_country(self, instance):
        if not instance.is_online and instance.location:
            return instance.location.country_id
        else:
            return super(AssignmentDocument, self).prepare_country(instance)

    def prepare_position(self, instance):
        if not instance.is_online and instance.location:
            position = instance.location.position
            return {'lat': position.get_y(), 'lon': position.get_x()}
