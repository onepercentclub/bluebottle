from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from .models import Reward
from .serializers import RewardSerializer
from bluebottle.utils.permissions import IsOwner
from bluebottle.utils.views import ListCreateAPIView, RetrieveUpdateDestroyAPIView


class RewardPagination(BluebottlePagination):
    page_size = 100


class RewardList(ListCreateAPIView):
    queryset = Reward.objects.all()
    serializer_class = RewardSerializer
    permission_classes = (IsOwner, )
    pagination_class = RewardPagination

    def get_queryset(self):
        qs = super(RewardList, self).get_queryset()
        project_slug = self.request.query_params.get('project', None)
        if project_slug:
            qs = qs.filter(project__slug=project_slug)
        return qs


class RewardDetail(RetrieveUpdateDestroyAPIView):
    queryset = Reward.objects.all()
    serializer_class = RewardSerializer
    permission_classes = (IsOwner, )
