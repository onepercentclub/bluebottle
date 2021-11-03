from django.db.models import Sum
from django.contrib.contenttypes.models import ContentType
from rest_framework.permissions import IsAuthenticated
from rest_framework_json_api.views import AutoPrefetchMixin

from bluebottle.activities.filters import ActivitySearchFilter
from bluebottle.activities.models import Activity, Contributor
from bluebottle.activities.permissions import ActivityOwnerPermission
from bluebottle.activities.serializers import (
    ActivitySerializer,
    ActivityTransitionSerializer,
    RelatedActivityImageSerializer,
    ActivityListSerializer,
    ContributorListSerializer
)
from bluebottle.files.models import RelatedImage
from bluebottle.files.views import ImageContentView
from bluebottle.funding.models import Donor
from bluebottle.deeds.models import DeedParticipant
from bluebottle.time_based.models import DateParticipant, PeriodParticipant
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission
)
from bluebottle.utils.views import (
    ListAPIView, JsonApiViewMixin, RetrieveUpdateDestroyAPIView,
    CreateAPIView
)


class ActivityList(JsonApiViewMixin, ListAPIView):
    queryset = Activity.objects.select_related(
        'owner',
        'initiative',
        'initiative__owner',
        'initiative__location',
        'initiative__theme',
        'initiative__place',
        'initiative__image',
        'initiative__location__country',
        'initiative__organization',
    ).prefetch_related('initiative__activity_managers')
    serializer_class = ActivityListSerializer
    model = Activity

    filter_backends = (
        ActivitySearchFilter,
    )

    permission_classes = (
        OneOf(ResourcePermission, ActivityOwnerPermission),
    )

    prefetch_for_includes = {
        'initiative': ['initiative'],
        'location': ['location'],
        'country': ['country'],
        'owner': ['owner'],
    }


class ActivityDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateDestroyAPIView):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    model = Activity
    lookup_field = 'pk'

    permission_classes = (
        OneOf(ResourcePermission, ActivityOwnerPermission),
    )

    prefetch_for_includes = {
        'initiative': ['initiative'],
        'location': ['location'],
        'owner': ['owner'],
        'contributors': ['contributors']
    }


class ContributorList(JsonApiViewMixin, ListAPIView):
    model = Contributor

    def get_queryset(self):
        return Contributor.objects.prefetch_related(
            'user', 'activity', 'contributions'
        ).instance_of(
            Donor,
            DateParticipant,
            PeriodParticipant,
            DeedParticipant
        ).filter(
            user=self.request.user
        ).exclude(
            status__in=['rejected', 'failed']
        ).exclude(
            donor__status__in=['new']
        ).order_by(
            '-created'
        ).annotate(
            total_duration=Sum('contributions__timecontribution__value'),
        )

    serializer_class = ContributorListSerializer

    pagination_class = None

    permission_classes = (IsAuthenticated, )


class ActivityImage(ImageContentView):
    queryset = Activity.objects
    field = 'image'


class RelatedActivityImageList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    def get_queryset(self):
        return RelatedImage.objects.filter(
            content_type=ContentType.objects.get_for_model(Activity)
        )

    serializer_class = RelatedActivityImageSerializer

    related_permission_classes = {
        'content_object': [
            OneOf(ResourcePermission, ActivityOwnerPermission),
        ]
    }

    permission_classes = []


class RelatedActivityImageContent(ImageContentView):
    def get_queryset(self):
        return RelatedImage.objects.filter(
            content_type__in=[
                ContentType.objects.get_by_natural_key('time_based', 'dateactivity'),
                ContentType.objects.get_by_natural_key('time_based', 'periodactivity'),
                ContentType.objects.get_by_natural_key('funding', 'funding'),
                ContentType.objects.get_by_natural_key('assignments', 'assignment'),
                ContentType.objects.get_by_natural_key('events', 'event'),
                ContentType.objects.get_by_natural_key('deeds', 'deed'),
                ContentType.objects.get_by_natural_key('collect', 'collectactivity'),
            ]
        )

    field = 'image'


class ActivityTransitionList(TransitionList):
    serializer_class = ActivityTransitionSerializer
    queryset = Activity.objects.all()
