from bluebottle.activities.utils import BaseContributionSerializer, BaseActivitySerializer
from bluebottle.jobs.models import Job, Applicant


class JobSerializer(BaseActivitySerializer):
    class Meta:
        model = Job
        fields = BaseActivitySerializer.Meta.fields + (
            'start', 'end', 'registration_deadline', 'capacity',
        )


class JobParticipantSerializer(BaseContributionSerializer):
    class Meta:
        model = Applicant
        fields = BaseContributionSerializer.Meta.fields + ('time_spent', )
