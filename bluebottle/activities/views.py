from django.contrib.contenttypes.models import ContentType

from rest_framework_json_api.views import AutoPrefetchMixin

from bluebottle.activities.models import Activity
from bluebottle.activities.filters import ActivitySearchFilter
from bluebottle.activities.serializers import (
    ActivitySerializer,
    ActivityReviewTransitionSerializer,
    RelatedActivityImageSerializer
)
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


class ActivityList(JsonApiViewMixin, AutoPrefetchMixin, ListAPIView):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
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
            content_type=ContentType.objects.get_for_model(Activity)
        )

    field = 'content_object'


class ActivityReviewTransitionList(TransitionList):
    serializer_class = ActivityReviewTransitionSerializer
    queryset = Activity.objects.all()
