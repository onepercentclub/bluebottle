import csv

from django.http.response import HttpResponse
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework_json_api.views import AutoPrefetchMixin
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from bluebottle.activities.permissions import ActivityPermission, ActivityTypePermission
from bluebottle.funding.authentication import DonationAuthentication
from bluebottle.funding.models import (
    Funding, Donation, Reward, Fundraiser,
    BudgetLine, PayoutAccount, PlainPayoutAccount
)
from bluebottle.funding.permissions import DonationOwnerPermission, PaymentPermission
from bluebottle.funding.serializers import (
    FundingSerializer, DonationSerializer, FundingTransitionSerializer,
    FundraiserSerializer, RewardSerializer, BudgetLineSerializer,
    DonationCreateSerializer, FundingListSerializer,
    PayoutAccountSerializer, PlainPayoutAccountSerializer,
    FundingPayoutsSerializer)
from bluebottle.payouts_dorado.permissions import IsFinancialMember
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.admin import prep_field
from bluebottle.utils.permissions import IsOwner
from bluebottle.utils.views import (
    ListAPIView, ListCreateAPIView, RetrieveUpdateAPIView, JsonApiViewMixin,
    CreateAPIView, RetrieveUpdateDestroyAPIView, PrivateFileView
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


class FundingPayoutDetails(RetrieveUpdateAPIView):
    # For Payout service
    queryset = Funding.objects.all()
    serializer_class = FundingPayoutsSerializer

    permission_classes = (IsFinancialMember,)

    def put(self, *args, **kwargs):
        status = self.request.data['status']
        # FIXME better trigger a request here where we check all payouts
        # related to this Funding.
        payout = self.get_object().payouts.first()
        if status == 'started':
            payout.transitions.start()
        if status == 'scheduled':
            payout.transitions.start()
        if status == 'new':
            payout.transitions.draft()
        if status == 'success':
            payout.transitions.succeed()
        if status == 'confirm':
            payout.transitions.succeed()
        payout.save()
        return HttpResponse(200)


class FundingTransitionList(TransitionList):
    serializer_class = FundingTransitionSerializer
    queryset = Funding.objects.all()

    prefetch_for_includes = {
        'resource': ['funding'],
    }


class PayoutAccountList(JsonApiViewMixin, AutoPrefetchMixin, ListAPIView):
    queryset = PayoutAccount.objects
    serializer_class = PayoutAccountSerializer

    permission_classes = (
        IsAuthenticated,
    )

    prefetch_for_includes = {
        'owner': ['owner'],
    }

    def get_queryset(self):
        return self.queryset.order_by('-created').filter(owner=self.request.user)


class PlainPayoutAccountList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    queryset = PlainPayoutAccount.objects.all()
    serializer_class = PlainPayoutAccountSerializer

    permission_classes = (
        IsAuthenticated,
    )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
        serializer.instance.transitions.submit()
        serializer.instance.save()


class PlainPayoutAccountDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = PlainPayoutAccount.objects.all()
    serializer_class = PlainPayoutAccountSerializer

    prefetch_for_includes = {
        'owner': ['owner'],
        'external_accounts': ['external_accounts'],
    }

    permission_classes = (IsAuthenticated, IsOwner, )

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
        serializer.instance.transitions.submit()
        serializer.instance.save()

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.status != serializer.instance.transitions.values.pending:
            serializer.instance.transitions.submit()
        serializer.instance.save()


class PlainPayoutAccountDocumentDetail(PrivateFileView):
    max_age = 15 * 60  # 15 minutes
    queryset = PlainPayoutAccount.objects
    relation = 'document'
    field = 'file'


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


class SupportersExportView(PrivateFileView):
    fields = (
        ('user__email', 'Email'),
        ('user__full_name', 'Name'),
        ('created', 'Donation Date'),
        ('amount_currency', 'Currency'),
        ('amount', 'Amount'),
        ('reward__title', 'Reward'),
    )

    model = Funding

    def get(self, request, *args, **kwargs):
        instance = self.get_object()

        response = HttpResponse()
        response['Content-Disposition'] = 'attachment; filename="supporters.csv"'
        response['Content-Type'] = 'text/csv'

        writer = csv.writer(response)

        writer.writerow([field[1] for field in self.fields])
        for donation in instance.contributions.filter(status='succeeded'):
            writer.writerow([
                prep_field(request, donation, field[0]) for field in self.fields
            ])

        return response
