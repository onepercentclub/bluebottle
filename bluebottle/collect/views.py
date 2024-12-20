from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from bluebottle.activities.permissions import (
    ActivityOwnerPermission, ActivityTypePermission, ActivityStatusPermission,
    DeleteActivityPermission, ContributorPermission, ActivitySegmentPermission
)
from bluebottle.activities.views import RelatedContributorListView
from bluebottle.collect.models import CollectActivity, CollectContributor, CollectType
from bluebottle.collect.serializers import (
    CollectActivitySerializer, CollectActivityTransitionSerializer, CollectContributorSerializer,
    CollectContributorTransitionSerializer, CollectTypeSerializer
)
from bluebottle.members.models import Member
from bluebottle.segments.views import ClosedSegmentActivityViewMixin
from bluebottle.time_based.permissions import CreateByEmailPermission
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission, TenantConditionalOpenClose
)
from bluebottle.utils.views import (
    RetrieveUpdateDestroyAPIView, ListAPIView, ListCreateAPIView, RetrieveUpdateAPIView,
    JsonApiViewMixin, ExportView, TranslatedApiViewMixin, RetrieveAPIView, NoPagination,
    IcalView
)


class CollectActivityListView(JsonApiViewMixin, ListCreateAPIView):
    queryset = CollectActivity.objects.all()
    serializer_class = CollectActivitySerializer

    permission_classes = (
        ActivityTypePermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
    )

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


class CollectActivityDetailView(JsonApiViewMixin, ClosedSegmentActivityViewMixin, RetrieveUpdateDestroyAPIView):
    permission_classes = (
        ActivityStatusPermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
        DeleteActivityPermission, ActivitySegmentPermission
    )

    queryset = CollectActivity.objects.all()
    serializer_class = CollectActivitySerializer


class CollectActivityTransitionList(TransitionList):
    serializer_class = CollectActivityTransitionSerializer
    queryset = CollectActivity.objects.all()


class CollectActivityRelatedCollectContributorList(RelatedContributorListView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    queryset = CollectContributor.objects.prefetch_related('user')
    serializer_class = CollectContributorSerializer


class CollectContributorList(JsonApiViewMixin, ListCreateAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
        CreateByEmailPermission
    )
    queryset = CollectContributor.objects.all()
    serializer_class = CollectContributorSerializer

    def perform_create(self, serializer):
        email = serializer.validated_data.pop('email', None)
        if email:
            user = Member.objects.filter(email__iexact=email).first()
            if not user:
                raise ValidationError(_('User with email address not found'))
        else:
            user = self.request.user

        self.check_related_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )
        self.check_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )
        if CollectContributor.objects.filter(user=user, activity=serializer.validated_data['activity']).exists():
            raise ValidationError(_('User already joined'), code="exists")

        serializer.save(user=user)


class CollectContributorDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission, ContributorPermission),
    )
    queryset = CollectContributor.objects.all()
    serializer_class = CollectContributorSerializer


class CollectContributorTransitionList(TransitionList):
    serializer_class = CollectContributorTransitionSerializer
    queryset = CollectContributor.objects.all()


class CollectContributorExportView(ExportView):
    fields = (
        ('user__email', 'Email'),
        ('user__full_name', 'Name'),
        ('created', 'Registration Date'),
        ('status', 'Status'),
    )

    model = CollectActivity

    def get_instances(self):
        return self.get_object().contributors.instance_of(
            CollectContributor
        )


class CollectTypeList(TranslatedApiViewMixin, JsonApiViewMixin, ListAPIView):
    serializer_class = CollectTypeSerializer
    queryset = CollectType.objects.filter(disabled=False)
    permission_classes = [TenantConditionalOpenClose, ]
    pagination_class = NoPagination

    def get_queryset(self):
        return super().get_queryset()


class CollectTypeDetail(TranslatedApiViewMixin, JsonApiViewMixin, RetrieveAPIView):
    serializer_class = CollectTypeSerializer
    queryset = CollectType.objects.filter(disabled=False)
    permission_classes = [TenantConditionalOpenClose, ]


class CollectIcalView(IcalView):
    queryset = CollectActivity.objects.exclude(
        status__in=['cancelled', 'deleted', 'rejected'],
    )

    @property
    def details(self):
        return super().details + _('\nCollecting {type}').format(type=self.get_object().collect_type)
