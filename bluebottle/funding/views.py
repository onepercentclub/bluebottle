from rest_framework_json_api.views import AutoPrefetchMixin

from bluebottle.activities.permissions import ActivityPermission, ActivityTypePermission
from bluebottle.funding.models import Funding, Donation
from bluebottle.funding.serializers import FundingSerializer, DonationSerializer, FundingTransitionSerializer
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.views import (
    ListCreateAPIView, RetrieveUpdateAPIView, JsonApiViewMixin,
    CreateAPIView,
)


class FundingList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
    queryset = Funding.objects.all()
    serializer_class = FundingSerializer

    permission_classes = (ActivityTypePermission, ActivityPermission,)

    prefetch_for_includes = {
        'initiative': ['initiative'],
        'owner': ['owner']
    }

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class FundingDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Funding.objects.all()
    serializer_class = FundingSerializer

    permission_classes = (ActivityTypePermission, ActivityPermission,)

    prefetch_for_includes = {
        'activitiy': ['initiative'],
        'owner': ['owner']
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
        'user': ['user']
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

    prefetch_for_includes = {
        'activity': ['activity'],
        'user': ['user']
    }
