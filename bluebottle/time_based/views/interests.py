from bluebottle.activities.permissions import (
    IsAdminPermission,
    RelatedActivityOwnerPermission,
)
from bluebottle.time_based.models import Interest
from bluebottle.time_based.permissions import RelatedActivityInterestListPermission
from bluebottle.time_based.serializers.interests import InterestSerializer
from bluebottle.time_based.views.mixins import AnonymizeMembersMixin
from bluebottle.utils.permissions import OneOf, ResourceOwnerPermission
from bluebottle.utils.views import (
    CreateAPIView,
    JsonApiViewMixin,
    ListAPIView,
    RetrieveUpdateDestroyAPIView,
)


class InterestList(JsonApiViewMixin, CreateAPIView):
    queryset = Interest.objects.prefetch_related('user', 'activity', 'slot')
    serializer_class = InterestSerializer
    permission_classes = (ResourceOwnerPermission,)


class InterestDetail(JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    queryset = Interest.objects.prefetch_related('user', 'activity', 'slot')
    serializer_class = InterestSerializer
    http_method_names = ['get', 'delete', 'head', 'options']
    permission_classes = (
        OneOf(
            ResourceOwnerPermission,
            RelatedActivityOwnerPermission,
            IsAdminPermission,
        ),
    )


class RelatedInterestListView(
    AnonymizeMembersMixin, JsonApiViewMixin, ListAPIView
):
    permission_classes = (RelatedActivityInterestListPermission,)
    queryset = Interest.objects.prefetch_related(
        'user', 'activity', 'slot'
    ).order_by('-created', 'pk')
    serializer_class = InterestSerializer
    activity_level_only = True

    def get_queryset(self):
        queryset = super().get_queryset()

        if 'slot_id' in self.kwargs:
            return queryset.filter(slot_id=self.kwargs['slot_id'])

        queryset = queryset.filter(activity_id=self.kwargs['activity_id'])
        if self.activity_level_only:
            queryset = queryset.filter(slot__isnull=True)
        return queryset


class DateRelatedInterestListView(RelatedInterestListView):
    activity_level_only = False


class DeadlineRelatedInterestList(RelatedInterestListView):
    pass


class ScheduleRelatedInterestList(RelatedInterestListView):
    pass


class PeriodicRelatedInterestList(RelatedInterestListView):
    pass

