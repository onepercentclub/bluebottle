from rest_framework_json_api.views import AutoPrefetchMixin
from rest_framework.pagination import PageNumberPagination

from bluebottle.activities.permissions import (
    ActivityOwnerPermission,
    ActivityTypePermission,
    ActivityStatusPermission,
    ApplicantPermission
)
from bluebottle.tasks.models import Skill
from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.assignments.serializers import (
    ApplicantSerializer, AssignmentTransitionSerializer,
    ApplicantTransitionSerializer, AssignmentSerializer,
    SkillSerializer
)
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission,
    TenantConditionalOpenClose
)
from bluebottle.utils.views import (
    ListCreateAPIView, RetrieveUpdateAPIView, JsonApiViewMixin, PrivateFileView,
    ListAPIView, TranslatedApiViewMixin, RetrieveAPIView
)


class AssignmentList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer

    permission_classes = (
        ActivityTypePermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
    )

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

    permission_classes = (
        ActivityStatusPermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
    )

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
        'user': ['user'],
        'document': ['document'],
    }

    def perform_create(self, serializer):
        self.check_related_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )

        self.check_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )

        serializer.save(user=self.request.user)


class ApplicantDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Applicant.objects.all()
    serializer_class = ApplicantSerializer

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission, ApplicantPermission),
    )

    prefetch_for_includes = {
        'activity': ['activity'],
        'user': ['user'],
        'document': ['document'],
    }


class ApplicantTransitionList(TransitionList):
    serializer_class = ApplicantTransitionSerializer
    queryset = Applicant.objects.all()
    prefetch_for_includes = {
        'resource': ['participant', 'participant__activity'],
    }


class ApplicantDocumentDetail(PrivateFileView):
    max_age = 15 * 60  # 15 minutes
    queryset = Applicant.objects
    relation = 'document'
    field = 'file'


class SkillPagination(PageNumberPagination):
    page_size = 10000


class SkillList(TranslatedApiViewMixin, JsonApiViewMixin, ListAPIView):
    serializer_class = SkillSerializer
    queryset = Skill.objects.filter(disabled=False)
    permission_classes = [TenantConditionalOpenClose, ]
    pagination_class = SkillPagination


class SkillDetail(TranslatedApiViewMixin, JsonApiViewMixin, RetrieveAPIView):
    serializer_class = SkillSerializer
    queryset = Skill.objects.filter(disabled=False)
    permission_classes = [TenantConditionalOpenClose, ]
