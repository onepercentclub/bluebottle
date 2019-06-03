from bluebottle.activities.utils import BaseContributionSerializer, BaseActivitySerializer
from bluebottle.assignments.models import Assignment, Applicant


class AssignmentSerializer(BaseActivitySerializer):
    class Meta:
        model = Assignment
        fields = BaseActivitySerializer.Meta.fields + (
            'end_time', 'registration_deadline', 'capacity',
        )

    class JSONAPIMeta(BaseContributionSerializer.JSONAPIMeta):
        included_resources = [
            'owner',
            'initiative',
            'place'
        ]
        resource_name = 'activities/assignments'


class AssignmentParticipantSerializer(BaseContributionSerializer):
    class Meta:
        model = Applicant
        fields = BaseContributionSerializer.Meta.fields + ('time_spent', )
