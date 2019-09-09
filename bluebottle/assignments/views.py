from bluebottle.activities.permissions import ActivityPermission, ActivityTypePermission
from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.assignments.serializers import AssignmentSerializer, ApplicantSerializer

from bluebottle.utils.views import RetrieveUpdateAPIView, ListCreateAPIView
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission
)


class AssignmentList(ListCreateAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer

    permission_classes = (ActivityTypePermission, ActivityPermission,)


class AssignmentDetail(RetrieveUpdateAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer

    permission_classes = (ActivityTypePermission, ActivityPermission,)


class ParticipantList(ListCreateAPIView):
    queryset = Applicant.objects.all()
    serializer_class = ApplicantSerializer

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )


class ParticipantDetail(RetrieveUpdateAPIView):
    queryset = Applicant.objects.all()
    serializer_class = ApplicantSerializer

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )
