import re

from django.http.response import HttpResponse
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework_json_api.views import AutoPrefetchMixin
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from bluebottle.activities.permissions import (
    ActivityOwnerPermission, ActivityTypePermission, ActivityStatusPermission,
    ActivitySegmentPermission
)
from bluebottle.funding.authentication import ClientSecretAuthentication
from bluebottle.funding.models import (
    Funding, Donor, Reward,
    BudgetLine, PayoutAccount, PlainPayoutAccount,
    Payout
)
from bluebottle.funding.permissions import PaymentPermission, DonorOwnerOrSucceededPermission
from bluebottle.funding.serializers import (
    FundingSerializer, DonorSerializer, FundingTransitionSerializer,
    RewardSerializer, BudgetLineSerializer,
    DonorCreateSerializer, PayoutAccountSerializer, PlainPayoutAccountSerializer,
    PayoutSerializer
)
from bluebottle.payouts_dorado.permissions import IsFinancialMember
from bluebottle.segments.models import SegmentType
from bluebottle.segments.views import ClosedSegmentActivityViewMixin
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.admin import prep_field
from bluebottle.utils.permissions import IsOwner, OneOf, ResourcePermission, IsActivityManager
from bluebottle.utils.views import (
    ListAPIView, ListCreateAPIView, RetrieveUpdateAPIView, JsonApiViewMixin,
    CreateAPIView, RetrieveUpdateDestroyAPIView, PrivateFileView
)
from bluebottle.utils.xlsx import generate_xlsx_response


class RewardList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    queryset = Reward.objects.all()
    serializer_class = RewardSerializer

    prefetch_for_includes = {
        'activity': ['activity'],
    }

    related_permission_classes = {
        'activity': [IsActivityManager]
    }

    permission_classes = [IsAuthenticatedOrReadOnly]


class RewardDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateDestroyAPIView):
    queryset = Reward.objects.all()
    serializer_class = RewardSerializer

    prefetch_for_includes = {
        'activity': ['activity'],
    }

    related_permission_classes = {
        'activity': [IsActivityManager]
    }

    permission_classes = [IsAuthenticatedOrReadOnly]


class BudgetLineList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    queryset = BudgetLine.objects.all()
    serializer_class = BudgetLineSerializer

    prefetch_for_includes = {
        'activity': ['activity'],
    }

    related_permission_classes = {
        'activity': [IsActivityManager]
    }

    permission_classes = [IsAuthenticatedOrReadOnly]


class BudgetLineDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateDestroyAPIView):
    queryset = BudgetLine.objects.all()
    serializer_class = BudgetLineSerializer

    prefetch_for_includes = {
        'activity': ['activity'],
    }

    related_permission_classes = {
        'activity': [IsActivityManager]
    }

    permission_classes = [IsAuthenticatedOrReadOnly]


class FundingList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
    queryset = Funding.objects.all()
    serializer_class = FundingSerializer

    permission_classes = (
        ActivityTypePermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
    )

    prefetch_for_includes = {
        'initiative': ['initiative'],
        'owner': ['owner'],
    }

    def perform_create(self, serializer):
        self.check_related_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )

        self.check_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )

        serializer.save(owner=self.request.user)


class FundingDetail(JsonApiViewMixin, ClosedSegmentActivityViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Funding.objects.select_related(
        'initiative', 'initiative__owner',
    ).prefetch_related('rewards')

    serializer_class = FundingSerializer
    permission_classes = (
        ActivityStatusPermission,
        ActivitySegmentPermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
    )

    prefetch_for_includes = {
        'initiative': ['initiative'],
        'owner': ['owner'],
        'rewards': ['reward'],
        'budgetlines': ['budgetlines'],
        'payment_methods': ['payment_methods'],
        'fundraisers': ['fundraisers']
    }


class PayoutDetails(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Payout.objects.all()
    serializer_class = PayoutSerializer

    authentication_classes = (TokenAuthentication,)

    permission_classes = (IsFinancialMember,)

    def perform_update(self, serializer):
        status = serializer.validated_data.pop('status')
        if status == 'reset':
            serializer.instance.states.reset()
        elif status in ['new', 'scheduled', 're_scheduled']:
            serializer.instance.states.schedule()
        elif status == 'started':
            serializer.instance.states.start()
        elif status in ['success', 'succeeded', 'confirmed']:
            serializer.instance.states.succeed()
        elif status in ['failed']:
            serializer.instance.states.fail()
        serializer.instance.save()
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
        serializer.instance.states.submit(save=True)


class PlainPayoutAccountDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = PlainPayoutAccount.objects.all()
    serializer_class = PlainPayoutAccountSerializer

    prefetch_for_includes = {
        'owner': ['owner'],
        'external_accounts': ['external_accounts'],
    }

    permission_classes = (IsAuthenticated, IsOwner,)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
        serializer.instance.states.submit()
        serializer.instance.save()

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.status == serializer.instance.states.new.value:
            serializer.instance.states.submit()
        serializer.instance.save()


class PlainPayoutAccountDocumentDetail(PrivateFileView):
    max_age = 15 * 60  # 15 minutes
    queryset = PlainPayoutAccount.objects
    relation = 'document'
    field = 'file'


class DonationList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    queryset = Donor.objects.all()
    serializer_class = DonorCreateSerializer

    permission_classes = (
    )

    prefetch_for_includes = {
        'activity': ['activity'],
        'user': ['user'],
        'reward': ['reward'],
        'fundraiser': ['fundraiser'],
    }

    def perform_create(self, serializer):
        serializer.save(user=(self.request.user if self.request.user.is_authenticated else None))


class DonationDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Donor.objects.all()
    serializer_class = DonorSerializer

    authentication_classes = (
        ClientSecretAuthentication,
        JSONWebTokenAuthentication
    )

    permission_classes = (
        DonorOwnerOrSucceededPermission,
    )

    prefetch_for_includes = {
        'activity': ['activity'],
        'user': ['user']
    }


class PaymentList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    permission_classes = (PaymentPermission,)

    prefetch_for_includes = {
        'donation': ['donation'],
        'user': ['user']
    }


class SupportersExportView(PrivateFileView):
    fields = (
        ('user__email', 'Email'),
        ('user__full_name', 'Name'),
        ('created', 'Date'),
        ('amount', 'Amount'),
        ('reward__title', 'Reward'),
    )

    model = Funding

    def get_segment_types(self):
        return SegmentType.objects.all()

    def get(self, request, *args, **kwargs):
        activity = self.get_object()
        filename = re.sub("[^\w\s\d]+", '-', activity.title)
        filename = 'participants for {}.xlsx'.format(filename)

        sheet = []
        title_row = [field[1] for field in self.fields]
        for segment_type in self.get_segment_types():
            title_row.append(segment_type.name)
        sheet.append(title_row)

        for t, donor in enumerate(
                activity.contributors.filter(status='succeeded').instance_of(Donor).prefetch_related('user__segments')
        ):
            row = [prep_field(request, donor, field[0]) for field in self.fields]
            for segment_type in self.get_segment_types():
                if donor.user:
                    segments = ", ".join(
                        donor.user.segments.filter(
                            segment_type=segment_type
                        ).values_list('name', flat=True)
                    )
                    row.append(segments)
            sheet.append(row)

        return generate_xlsx_response(filename=filename, data=sheet)
