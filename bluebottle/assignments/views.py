from rest_framework_json_api.views import AutoPrefetchMixin

from bluebottle.activities.permissions import ActivityPermission, ActivityTypePermission
from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.assignments.serializers import AssignmentSerializer, ApplicantSerializer

from bluebottle.utils.views import RetrieveUpdateAPIView, ListCreateAPIView, JsonApiViewMixin
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission
)


class AssignmentList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer

    permission_classes = (ActivityTypePermission, ActivityPermission,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class AssignmentDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer

    permission_classes = (ActivityTypePermission, ActivityPermission,)


class ApplicantList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
    queryset = Applicant.objects.all()
    serializer_class = ApplicantSerializer

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )


class ApplicantDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Applicant.objects.all()
    serializer_class = ApplicantSerializer

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )
