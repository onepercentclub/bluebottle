from django.db.models import Q

from bluebottle.activities.permissions import (
    IsAdminPermission,
    RelatedActivityOwnerPermission,
)
from bluebottle.activities.views import ContributionPagination
from bluebottle.time_based.models import Interest
from bluebottle.time_based.permissions import RelatedActivityInterestListPermission
from bluebottle.time_based.serializers.interests import InterestSerializer
from bluebottle.time_based.views.mixins import AnonymizeMembersMixin
from bluebottle.utils.permissions import OneOf, ResourceOwnerPermission
from bluebottle.utils.views import (
    JsonApiViewMixin,
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)

INTEREST_VISIBLE_STATUSES = ('open', 'full')


class InterestList(JsonApiViewMixin, ListCreateAPIView):
    queryset = Interest.objects.prefetch_related('user', 'activity', 'slot')
    serializer_class = InterestSerializer
    permission_classes = (ResourceOwnerPermission,)
    pagination_class = ContributionPagination

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.method != 'GET':
            return queryset

        return queryset.filter(
            user=self.request.user,
        ).filter(
            Q(
                slot__isnull=True,
                activity__status__in=INTEREST_VISIBLE_STATUSES,
            ) | Q(
                slot__isnull=False,
                slot__status__in=INTEREST_VISIBLE_STATUSES,
                activity__status__in=INTEREST_VISIBLE_STATUSES,
            )
        ).select_related(
            'slot',
        ).prefetch_related(
            'activity',
            'activity__image',
            'activity__initiative',
            'activity__initiative__image',
        ).order_by('-created')


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
