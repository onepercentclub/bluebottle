from rest_framework import generics

from bluebottle.rewards.models import Reward
from .serializers import RewardSerializer
from .models import Quote
from .serializers import QuoteSerializer
from django.utils.timezone import now
from django.db.models import Q


# API views

class ProjectRewardList(generics.ListAPIView):
    model = Reward
    serializer_class = RewardSerializer
    paginate_by = 100

    def get_queryset(self):
        qs = super(ProjectRewardList, self).get_queryset()
        qs = qs.filter(project__slug=self.request)
        return qs
