from django.contrib.contenttypes.models import ContentType

from rest_framework_json_api.views import AutoPrefetchMixin

from bluebottle.activities.models import Activity
from bluebottle.activities.filters import ActivitySearchFilter
from bluebottle.activities.serializers import (
    ActivitySerializer,
    ActivityReviewTransitionSerializer,
    RelatedActivityImageSerializer,
    ActivityListSerializer)
from bluebottle.files.views import ImageContentView
from bluebottle.files.models import RelatedImage
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission
)
from bluebottle.utils.views import (
    ListAPIView, JsonApiViewMixin, RetrieveUpdateDestroyAPIView,
    CreateAPIView
)


class ActivityList(JsonApiViewMixin, ListAPIView):
    queryset = Activity.objects.select_related(
        'owner', 'initiative',
        'initiative__owner',
        'initiative__location', 'initiative__theme',
        'initiative__place', 'initiative__image',
        'initiative__activity_manager',
        'initiative__location__country',
        'initiative__organization',
    )
    serializer_class = ActivityListSerializer
    model = Activity

    filter_backends = (
        ActivitySearchFilter,
    )

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
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
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    prefetch_for_includes = {
        'initiative': ['initiative'],
        'location': ['location'],
        'owner': ['owner'],
        'contributions': ['contributions']
    }


class RelatedActivityImageList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    def get_queryset(self):
        return RelatedImage.objects.filter(
            content_type=ContentType.objects.get_for_model(Activity)
        )

    serializer_class = RelatedActivityImageSerializer

    related_permission_classes = {
        'content_object': [
            OneOf(ResourcePermission, ResourceOwnerPermission),
        ]
    }

    permission_classes = []


class RelatedActivityImageContent(ImageContentView):
    def get_queryset(self):
        return RelatedImage.objects.filter(
            content_type__in=[
                ContentType.objects.get_by_natural_key('events', 'event'),
                ContentType.objects.get_by_natural_key('funding', 'funding'),
                ContentType.objects.get_by_natural_key('assignments', 'assignment'),
            ]
        )

    field = 'image'


class ActivityReviewTransitionList(TransitionList):
    serializer_class = ActivityReviewTransitionSerializer
    queryset = Activity.objects.all()
