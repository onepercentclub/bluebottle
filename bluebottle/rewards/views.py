from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, RelatedResourceOwnerPermission
)
from bluebottle.utils.views import (
    ListCreateAPIView, RetrieveUpdateDestroyAPIView, OwnerListViewMixin
)

from .models import Reward
from .permissions import NoDonationsOrReadOnly
from .serializers import RewardSerializer


class RewardPagination(BluebottlePagination):
    page_size = 100


class RewardList(OwnerListViewMixin, ListCreateAPIView):
    queryset = Reward.objects.all()
    serializer_class = RewardSerializer
    permission_classes = (
        OneOf(ResourcePermission, RelatedResourceOwnerPermission),
    )
    pagination_class = RewardPagination

    owner_filter_field = 'project__owner'

    def get_queryset(self):
        qs = super(RewardList, self).get_queryset()

        project_slug = self.request.query_params.get('project', None)
        if project_slug:
            qs = qs.filter(project__slug=project_slug)
        return qs


class RewardDetail(RetrieveUpdateDestroyAPIView):
    queryset = Reward.objects.all()
    serializer_class = RewardSerializer

    permission_classes = (
        OneOf(ResourcePermission, RelatedResourceOwnerPermission),
        NoDonationsOrReadOnly
    )
