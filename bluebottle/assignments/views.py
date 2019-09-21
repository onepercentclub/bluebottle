from rest_framework_json_api.views import AutoPrefetchMixin

from bluebottle.activities.permissions import ActivityPermission, ActivityTypePermission
from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.assignments.permissions import ApplicantDocumentPermission
from bluebottle.assignments.serializers import ApplicantSerializer, \
    AssignmentTransitionSerializer, ApplicantTransitionSerializer, AssignmentListSerializer, AssignmentSerializer
from bluebottle.files.views import FileContentView
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission)
from bluebottle.utils.views import (
    ListCreateAPIView, RetrieveUpdateAPIView, JsonApiViewMixin)


class AssignmentList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentListSerializer
    filter_fields = ('owner__id', )

    permission_classes = (ActivityTypePermission, ActivityPermission,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    prefetch_for_includes = {
        'initiative': ['initiative'],
        'location': ['location'],
        'owner': ['owner'],
    }


class AssignmentDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer

    permission_classes = (ActivityTypePermission, ActivityPermission,)

    prefetch_for_includes = {
        'initiative': ['initiative'],
        'location': ['location'],
        'owner': ['owner'],
        'contributions': ['contributions']
    }


class AssignmentTransitionList(TransitionList):
    serializer_class = AssignmentTransitionSerializer
    queryset = Assignment.objects.all()

    prefetch_for_includes = {
        'resource': ['funding'],
    }


class ApplicantList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
    queryset = Applicant.objects.all()
    serializer_class = ApplicantSerializer

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    prefetch_for_includes = {
        'assignment': ['assignment'],
        'document': ['document'],
    }

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ApplicantDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Applicant.objects.all()
    serializer_class = ApplicantSerializer

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    prefetch_for_includes = {
        'assignment': ['assignment'],
        'document': ['document'],
    }


class ApplicantTransitionList(TransitionList):
    serializer_class = ApplicantTransitionSerializer
    queryset = Applicant.objects.all()
    prefetch_for_includes = {
        'resource': ['participant', 'participant__activity'],
    }


class ApplicantDocumentDetail(FileContentView):
    queryset = Applicant.objects
    field = 'document'

    permission_classes = (
        ApplicantDocumentPermission,
    )
