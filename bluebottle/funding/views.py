from rest_framework_json_api.views import AutoPrefetchMixin

from bluebottle.activities.permissions import ActivityPermission, ActivityTypePermission
from bluebottle.funding.models import Funding, Donation
from bluebottle.funding.models import (
    Reward, Fundraiser, BudgetLine,
)
from bluebottle.funding.serializers import (
    FundingSerializer, DonationSerializer, FundingTransitionSerializer
)
from bluebottle.funding.serializers import (
    FundraiserSerializer, RewardSerializer, BudgetLineSerializer
)
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.permissions import IsOwner
from bluebottle.utils.views import (
    ListCreateAPIView, RetrieveUpdateAPIView, JsonApiViewMixin,
    CreateAPIView,
)


class RewardList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    queryset = Reward.objects.all()
    serializer_class = RewardSerializer

    prefetch_for_includes = {
        'activity': ['activity'],
    }

    permission_classes = []


class RewardDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Reward.objects.all()
    serializer_class = RewardSerializer

    prefetch_for_includes = {
        'activity': ['activity'],
    }

    permission_classes = []


class FundraiserList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    queryset = Fundraiser.objects.all()
    serializer_class = FundraiserSerializer

    prefetch_for_includes = {
        'owner': ['owner'],
        'activity': ['activity'],
    }

    permission_classes = []

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class FundraiserDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Fundraiser.objects.all()
    serializer_class = FundraiserSerializer

    prefetch_for_includes = {
        'owner': ['owner'],
        'activity': ['activity'],
    }

    permission_classes = []


class BudgetLineList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    queryset = BudgetLine.objects.all()
    serializer_class = BudgetLineSerializer

    prefetch_for_includes = {
        'activity': ['activity'],
    }

    permission_classes = []


class BudgetLineDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = BudgetLine.objects.all()
    serializer_class = BudgetLineSerializer

    prefetch_for_includes = {
        'activity': ['activity'],
    }

    permission_classes = []


class FundingList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
    queryset = Funding.objects.all()
    serializer_class = FundingSerializer

    permission_classes = (ActivityTypePermission, ActivityPermission,)

    prefetch_for_includes = {
        'initiative': ['initiative'],
        'owner': ['owner']
    }

    permission_classes = []

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class FundingDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Funding.objects.all()
    serializer_class = FundingSerializer

    permission_classes = []

    prefetch_for_includes = {
        'activitiy': ['initiative'],
        'owner': ['owner'],
        'rewards': ['reward'],
        'budgetlines': ['budgetlines'],
        'fundraisers': ['fundraisers']
    }


class FundingTransitionList(TransitionList):
    serializer_class = FundingTransitionSerializer
    queryset = Funding.objects.all()

    prefetch_for_includes = {
        'resource': ['funding'],
    }


class DonationList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
    queryset = Donation.objects.all()
    serializer_class = DonationSerializer

    permission_classes = (
    )

    prefetch_for_includes = {
        'activity': ['activity'],
        'user': ['user'],
        'reward': ['reward'],
        'fundraiser': ['fundraiser'],
    }

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DonationDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Donation.objects.all()
    serializer_class = DonationSerializer

    permission_classes = (
    )

    prefetch_for_includes = {
        'activity': ['activity'],
        'user': ['user']
    }


class PaymentList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    permission_classes = []

    related_permission_classes = {
        'donation': [IsOwner]
    }

    prefetch_for_includes = {
        'donation': ['donation'],
        'user': ['user']
    }
