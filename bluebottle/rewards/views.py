from rest_framework import generics

from bluebottle.bb_projects.permissions import IsProjectOwnerOrReadOnly
from .permissions import NoDonationsOrReadOnly
from .models import Reward
from .serializers import RewardSerializer


class RewardList(generics.ListCreateAPIView):
    queryset = Reward.objects.all()
    serializer_class = RewardSerializer
    permission_classes = (IsProjectOwnerOrReadOnly, )
    paginate_by = 100

    def get_queryset(self):
        qs = super(RewardList, self).get_queryset()
        project_slug = self.request.QUERY_PARAMS.get('project', None)
        if project_slug:
            qs = qs.filter(project__slug=project_slug)
        return qs


class RewardDetail(generics.RetrieveDestroyAPIView):
    queryset = Reward.objects.all()
    serializer_class = RewardSerializer
    permission_classes = (IsProjectOwnerOrReadOnly, NoDonationsOrReadOnly)
