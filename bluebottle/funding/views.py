from django.http import Http404
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework_json_api.views import AutoPrefetchMixin
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from bluebottle.activities.permissions import ActivityPermission, ActivityTypePermission
from bluebottle.funding.models import (
    Funding, Donation, Reward, Fundraiser,
    BudgetLine,
    PlainPayoutAccount, PlainBankAccount)
from bluebottle.funding.serializers import (
    FundingSerializer, DonationSerializer, FundingTransitionSerializer,
    FundraiserSerializer, RewardSerializer, BudgetLineSerializer,
    DonationCreateSerializer,
    FundingListSerializer, PlainPayoutAccountSerializer, PlainBankAccountSerializer)
from bluebottle.funding.authentication import DonationAuthentication
from bluebottle.funding.permissions import DonationOwnerPermission, PaymentPermission
from bluebottle.members.models import Member
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.permissions import IsOwner, IsAuthenticated
from bluebottle.utils.views import (
    ListCreateAPIView, RetrieveUpdateAPIView, JsonApiViewMixin,
    CreateAPIView, RetrieveUpdateDestroyAPIView
)


class RewardList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    queryset = Reward.objects.all()
    serializer_class = RewardSerializer

    prefetch_for_includes = {
        'activity': ['activity'],
    }

    related_permission_classes = {
        'activity': [IsOwner]
    }

    permission_classes = [IsAuthenticatedOrReadOnly]


class RewardDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateDestroyAPIView):
    queryset = Reward.objects.all()
    serializer_class = RewardSerializer

    prefetch_for_includes = {
        'activity': ['activity'],
    }

    related_permission_classes = {
        'activity': [IsOwner]
    }

    permission_classes = [IsAuthenticatedOrReadOnly]


class FundraiserList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    queryset = Fundraiser.objects.all()
    serializer_class = FundraiserSerializer

    prefetch_for_includes = {
        'owner': ['owner'],
        'activity': ['activity'],
    }

    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class FundraiserDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Fundraiser.objects.all()
    serializer_class = FundraiserSerializer

    prefetch_for_includes = {
        'owner': ['owner'],
        'initiative': ['initiative'],
        'location': ['location'],
        'contributions': ['contributions']
    }

    permission_classes = [IsAuthenticatedOrReadOnly]


class BudgetLineList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    queryset = BudgetLine.objects.all()
    serializer_class = BudgetLineSerializer

    prefetch_for_includes = {
        'activity': ['activity'],
    }

    related_permission_classes = {
        'activity': [IsOwner]
    }

    permission_classes = [IsAuthenticatedOrReadOnly]


class BudgetLineDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateDestroyAPIView):
    queryset = BudgetLine.objects.all()
    serializer_class = BudgetLineSerializer

    prefetch_for_includes = {
        'activity': ['activity'],
    }

    related_permission_classes = {
        'activity': [IsOwner]
    }

    permission_classes = [IsAuthenticatedOrReadOnly]


class FundingList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
    queryset = Funding.objects.all()
    serializer_class = FundingListSerializer

    permission_classes = (ActivityTypePermission, ActivityPermission,)

    prefetch_for_includes = {
        'initiative': ['initiative'],
        'owner': ['owner'],
    }

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class FundingDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Funding.objects.all()
    serializer_class = FundingSerializer

    permission_classes = (ActivityPermission,)

    prefetch_for_includes = {
        'initiative': ['initiative'],
        'owner': ['owner'],
        'rewards': ['reward'],
        'budgetlines': ['budgetlines'],
        'payment_methods': ['payment_methods'],
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
    serializer_class = DonationCreateSerializer

    permission_classes = (
    )

    prefetch_for_includes = {
        'activity': ['activity'],
        'user': ['user'],
        'reward': ['reward'],
        'fundraiser': ['fundraiser'],
    }

    def perform_create(self, serializer):
        serializer.save(user=(self.request.user if self.request.user.is_authenticated() else None))


class DonationDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Donation.objects.all()
    serializer_class = DonationSerializer

    authentication_classes = (
        JSONWebTokenAuthentication, DonationAuthentication,
    )

    permission_classes = (DonationOwnerPermission, )

    prefetch_for_includes = {
        'activity': ['activity'],
        'user': ['user']
    }


class PaymentList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    permission_classes = (PaymentPermission, )

    prefetch_for_includes = {
        'donation': ['donation'],
        'user': ['user']
    }


# Payout accounts

class PlainPayoutAccountView(JsonApiViewMixin, AutoPrefetchMixin, CreateModelMixin, RetrieveUpdateAPIView):
    queryset = PlainPayoutAccount.objects.all()
    serializer_class = PlainPayoutAccountSerializer

    prefetch_for_includes = {
        'owner': ['owner'],
        'external_accounts': ['external_accounts'],
    }

    permission_classes = (IsAuthenticated, IsOwner, )

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def get_object(self):
        try:
            obj = self.request.user.funding_payout_account
        except Member.funding_payout_account.RelatedObjectDoesNotExist:
            raise Http404

        self.check_object_permissions(self.request, obj)
        return obj


class PlainBankAccountView(JsonApiViewMixin, AutoPrefetchMixin, CreateModelMixin, RetrieveUpdateAPIView):
    queryset = PlainBankAccount.objects.all()
    serializer_class = PlainBankAccountSerializer

    prefetch_for_includes = {
        'owner': ['owner'],
    }

    permission_classes = (IsAuthenticated, IsOwner, )

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def get_object(self):
        try:
            obj = self.request.user.funding_payout_account
        except Member.funding_payout_account.RelatedObjectDoesNotExist:
            raise Http404

        self.check_object_permissions(self.request, obj)
        return obj
