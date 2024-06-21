from rest_framework import filters

from bluebottle.activities.models import Activity
from bluebottle.activities.permissions import ContributorPermission
from bluebottle.activities.views import RelatedContributorListView
from bluebottle.time_based.models import DeadlineRegistration, PeriodicRegistration, ScheduleRegistration, \
    TeamScheduleRegistration
from bluebottle.time_based.serializers import (
    DeadlineRegistrationSerializer,
    DeadlineRegistrationTransitionSerializer,
    PeriodicRegistrationSerializer,
    PeriodicRegistrationTransitionSerializer,
    ScheduleRegistrationSerializer,
    ScheduleRegistrationTransitionSerializer,
    TeamScheduleRegistrationSerializer,
    TeamScheduleRegistrationTransitionSerializer
)
from bluebottle.time_based.views.mixins import (
    AnonimizeMembersMixin, FilterRelatedUserMixin,
    RequiredQuestionsMixin
)
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.permissions import (
    OneOf,
    ResourceOwnerPermission,
    ResourcePermission, IsAuthenticated, IsOwnerOrReadOnly,
)
from bluebottle.utils.views import (
    JsonApiViewMixin, ListAPIView, CreateAPIView, PrivateFileView,
    RetrieveUpdateAPIView
)


class RegistrationList(JsonApiViewMixin, RequiredQuestionsMixin, CreateAPIView):

    permission_classes = (
        OneOf(ResourcePermission, IsAuthenticated),
    )


class DeadlineRegistrationList(RegistrationList):
    queryset = DeadlineRegistration.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = DeadlineRegistrationSerializer


class ScheduleRegistrationList(RegistrationList):
    queryset = ScheduleRegistration.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = ScheduleRegistrationSerializer


class TeamScheduleRegistrationList(RegistrationList):
    queryset = TeamScheduleRegistration.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = TeamScheduleRegistrationSerializer


class PeriodicRegistrationList(RegistrationList):
    queryset = PeriodicRegistration.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = PeriodicRegistrationSerializer


class RelatedRegistrationListView(
    RelatedContributorListView, ListAPIView, AnonimizeMembersMixin, FilterRelatedUserMixin
):
    @property
    def owners(self):
        if 'activity_id' in self.kwargs:
            activity = Activity.objects.get(pk=self.kwargs['activity_id'])
            return [activity.owner] + list(activity.initiative.activity_managers.all())

    search_fields = ['user__first_name', 'user__last_name']
    filter_backends = [filters.SearchFilter]

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    def get_queryset(self):
        queryset = super().get_queryset()

        my = self.request.query_params.get('filter[my]')

        if my:
            if self.request.user.is_authenticated:
                queryset = queryset.filter(user=self.request.user)
            else:
                queryset = queryset.none()

        return queryset.filter(
            activity_id=self.kwargs['activity_id']
        )


class DeadlineRelatedRegistrationList(RelatedRegistrationListView):
    queryset = DeadlineRegistration.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = DeadlineRegistrationSerializer


class ScheduleRelatedRegistrationList(RelatedRegistrationListView):
    queryset = ScheduleRegistration.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = ScheduleRegistrationSerializer


class TeamScheduleRelatedRegistrationList(RelatedRegistrationListView):
    queryset = TeamScheduleRegistration.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = TeamScheduleRegistrationSerializer
    permission_classes = (
        IsAuthenticated, IsOwnerOrReadOnly
    )


class PeriodicRelatedRegistrationList(RelatedRegistrationListView):
    queryset = PeriodicRegistration.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = PeriodicRegistrationSerializer


class RegistrationDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission, ContributorPermission),
    )


class DeadlineRegistrationDetail(RegistrationDetail):
    queryset = DeadlineRegistration.objects.all()
    serializer_class = DeadlineRegistrationSerializer


class ScheduleRegistrationDetail(RegistrationDetail):
    queryset = ScheduleRegistration.objects.all()
    serializer_class = ScheduleRegistrationSerializer


class TeamScheduleRegistrationDetail(RegistrationDetail):
    queryset = TeamScheduleRegistration.objects.all()
    serializer_class = TeamScheduleRegistrationSerializer
    permission_classes = (
        IsAuthenticated, IsOwnerOrReadOnly
    )


class PeriodicRegistrationDetail(RegistrationDetail):
    queryset = PeriodicRegistration.objects.all()
    serializer_class = PeriodicRegistrationSerializer


class DeadlineRegistrationTransitionList(TransitionList):
    serializer_class = DeadlineRegistrationTransitionSerializer
    queryset = DeadlineRegistration.objects.all()


class ScheduleRegistrationTransitionList(TransitionList):
    serializer_class = ScheduleRegistrationTransitionSerializer
    queryset = ScheduleRegistration.objects.all()


class TeamScheduleRegistrationTransitionList(TransitionList):
    serializer_class = TeamScheduleRegistrationTransitionSerializer
    queryset = TeamScheduleRegistration.objects.all()


class PeriodicRegistrationTransitionList(TransitionList):
    serializer_class = PeriodicRegistrationTransitionSerializer
    queryset = PeriodicRegistration.objects.all()


class RegistrationDocumentDetail(PrivateFileView):
    max_age = 15 * 60  # 15 minutes
    relation = 'document'
    field = 'file'


class DeadlineRegistrationDocumentDetail(RegistrationDocumentDetail):
    queryset = DeadlineRegistration.objects


class ScheduleRegistrationDocumentDetail(RegistrationDocumentDetail):
    queryset = ScheduleRegistration.objects


class PeriodicRegistrationDocumentDetail(RegistrationDocumentDetail):
    queryset = PeriodicRegistration.objects
