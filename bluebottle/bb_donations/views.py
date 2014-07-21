import logging
from bluebottle.donations.models import Donation
from bluebottle.donations.serializers import DonationSerializer
from django.contrib.auth.models import AnonymousUser
from rest_framework import generics
from django.utils.translation import ugettext as _

from bluebottle.utils.utils import get_project_model

PROJECT_MODEL = get_project_model()

logger = logging.getLogger(__name__)


class DonationList(generics.ListCreateAPIView):
    model = Donation
    serializer_class = DonationSerializer
    # FIXME: Add permission for OrderOwner

    def get_queryset(self):
        qs = super(DonationList, self).get_queryset()
        return qs.filter(user=self.request.user)


class DonationDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Donation
    serializer_class = DonationSerializer
    # FIXME: Add permission for OrderOwner


