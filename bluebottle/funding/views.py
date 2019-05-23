from bluebottle.activities.permissions import ActivityPermission, ActivityTypePermission

from bluebottle.utils.views import ListCreateAPIView, RetrieveUpdateAPIView
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission
)

from bluebottle.funding.models import Funding, Donation
from bluebottle.funding.serializers import FundingSerializer, DonationSerializer


class FundingList(ListCreateAPIView):
    queryset = Funding.objects.all()
    serializer_class = FundingSerializer

    lookup_field = 'slug'

    permission_classes = (ActivityTypePermission, ActivityPermission,)


class FundingDetail(RetrieveUpdateAPIView):
    queryset = Funding.objects.all()
    serializer_class = FundingSerializer

    lookup_field = 'slug'

    permission_classes = (ActivityTypePermission, ActivityPermission,)


class DonationList(ListCreateAPIView):
    queryset = Donation.objects.all()
    serializer_class = DonationSerializer

    lookup_field = 'slug'

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )


class DonationDetail(RetrieveUpdateAPIView):
    queryset = Donation.objects.all()
    serializer_class = DonationSerializer

    lookup_field = 'slug'

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )
