from bluebottle.activities.serializers.serializers import ActivityImageSerializer
from bluebottle.activity_links.models import (
    LinkedActivity, LinkedCollectCampaign, LinkedDateActivity, LinkedDeadlineActivity,
    LinkedDeed, LinkedFunding, LinkedGrantApplication, LinkedPeriodicActivity,
    LinkedScheduleActivity,
)
from bluebottle.activity_links.serializers import (
    LinkedCollectCampaignJSONAPISerializer, LinkedDateActivityJSONAPISerializer,
    LinkedDeadlineActivityJSONAPISerializer, LinkedDeedJSONAPISerializer,
    LinkedFundingJSONAPISerializer, LinkedGrantApplicationJSONAPISerializer,
    LinkedPeriodicActivityJSONAPISerializer, LinkedScheduleActivityJSONAPISerializer,
)
from bluebottle.files.views import ImageContentView
from bluebottle.utils.permissions import TenantConditionalOpenClose
from bluebottle.utils.views import JsonApiViewMixin, RetrieveAPIView


class LinkedActivityImage(ImageContentView):
    queryset = LinkedActivity.objects
    field = 'image'
    allowed_sizes = ActivityImageSerializer.sizes


class BaseLinkDetail(JsonApiViewMixin, RetrieveAPIView):
    permission_classes = (
        TenantConditionalOpenClose,
    )


class DeedLinkDetail(BaseLinkDetail):
    queryset = LinkedDeed.objects.all()
    serializer_class = LinkedDeedJSONAPISerializer


class CollectLinkDetail(BaseLinkDetail):
    queryset = LinkedCollectCampaign.objects.all()
    serializer_class = LinkedCollectCampaignJSONAPISerializer


class FundingLinkDetail(BaseLinkDetail):
    queryset = LinkedFunding.objects.all()
    serializer_class = LinkedFundingJSONAPISerializer


class GrantApplicationLinkDetail(BaseLinkDetail):
    queryset = LinkedGrantApplication.objects.all()
    serializer_class = LinkedGrantApplicationJSONAPISerializer


class DeadlineLinkDetail(BaseLinkDetail):
    queryset = LinkedDeadlineActivity.objects.all()
    serializer_class = LinkedDeadlineActivityJSONAPISerializer


class DateLinkDetail(BaseLinkDetail):
    queryset = LinkedDateActivity.objects.prefetch_related('slots', 'slots__location')
    serializer_class = LinkedDateActivityJSONAPISerializer


class PeriodicLinkDetail(BaseLinkDetail):
    queryset = LinkedPeriodicActivity.objects.all()
    serializer_class = LinkedPeriodicActivityJSONAPISerializer


class ScheduleLinkDetail(BaseLinkDetail):
    queryset = LinkedScheduleActivity.objects.all()
    serializer_class = LinkedScheduleActivityJSONAPISerializer
