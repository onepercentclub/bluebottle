from rest_framework import filters

from bluebottle.activities.models import Activity
from bluebottle.activities.permissions import ContributorPermission
from bluebottle.activities.views import RelatedContributorListView
from bluebottle.time_based.models import DeadlineRegistration, PeriodicRegistration
from bluebottle.time_based.serializers import (
    DeadlineRegistrationSerializer, DeadlineRegistrationTransitionSerializer,
    PeriodicRegistrationSerializer, PeriodicRegistrationTransitionSerializer
)
from bluebottle.utils.permissions import (
    OneOf,
    ResourceOwnerPermission,
    ResourcePermission,
)
from bluebottle.utils.views import (
    JsonApiViewMixin, ListAPIView, CreateAPIView, PrivateFileView,
    RetrieveUpdateAPIView
)
from bluebottle.time_based.views.mixins import (
    AnonimizeMembersMixin, FilterRelatedUserMixin,
    RequiredQuestionsMixin
)
from bluebottle.transitions.views import TransitionList


class RegistrationList(JsonApiViewMixin, RequiredQuestionsMixin, CreateAPIView):

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )


class DeadlineRegistrationList(RegistrationList):
    queryset = DeadlineRegistration.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = DeadlineRegistrationSerializer


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
            queryset = queryset.filter(user=self.request.user)

        return queryset.filter(
            activity_id=self.kwargs['activity_id']
        )


class DeadlineRelatedRegistrationList(RelatedRegistrationListView):
    queryset = DeadlineRegistration.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = DeadlineRegistrationSerializer


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


class PeriodicRegistrationDetail(RegistrationDetail):
    queryset = PeriodicRegistration.objects.all()
    serializer_class = PeriodicRegistrationSerializer


class DeadlineRegistrationTransitionList(TransitionList):
    serializer_class = DeadlineRegistrationTransitionSerializer
    queryset = DeadlineRegistration.objects.all()


class PeriodicRegistrationTransitionList(TransitionList):
    serializer_class = PeriodicRegistrationTransitionSerializer
    queryset = PeriodicRegistration.objects.all()


class RegistrationDocumentDetail(PrivateFileView):
    max_age = 15 * 60  # 15 minutes
    relation = 'document'
    field = 'file'


class DeadlineRegistrationDocumentDetail(RegistrationDocumentDetail):
    queryset = DeadlineRegistration.objects


class PeriodicRegistrationDocumentDetail(RegistrationDocumentDetail):
    queryset = PeriodicRegistration.objects
