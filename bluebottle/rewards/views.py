from rest_framework import generics

from bluebottle.bb_projects.permissions import IsProjectOwnerOrReadOnly
from .models import Reward
from .serializers import RewardSerializer


class ProjectRewardList(generics.ListCreateAPIView):
    model = Reward
    serializer_class = RewardSerializer
    permission_classes = (IsProjectOwnerOrReadOnly, )
    paginate_by = 100

    def get_queryset(self):
        project_slug = self.kwargs.get('project_slug', None)
        qs = super(ProjectRewardList, self).get_queryset()
        qs = qs.filter(project__slug=project_slug)
        return qs


class ProjectRewardDetail(generics.RetrieveDestroyAPIView):
    model = Reward
    serializer_class = RewardSerializer

    def get_queryset(self):
        project_slug = self.kwargs.get('project_slug', None)
        qs = super(ProjectRewardDetail, self).get_queryset()
        qs = qs.filter(project__slug=project_slug)
        return qs
