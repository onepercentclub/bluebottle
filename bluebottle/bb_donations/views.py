import logging
from bluebottle.bb_donations.serializers import MyDonationSerializer
from .models import Donation
from .serializers import DonationSerializer
from django.contrib.auth.models import AnonymousUser
from rest_framework import generics
from django.utils.translation import ugettext as _

from bluebottle.utils.utils import get_project_model

PROJECT_MODEL = get_project_model()

logger = logging.getLogger(__name__)


class DonationList(generics.ListAPIView):
    model = Donation
    serializer_class = DonationSerializer
    # FIXME: Filter on donations that are viewable (pending & paid)


class DonationDetail(generics.RetrieveAPIView):
    model = Donation
    serializer_class = DonationSerializer
    # FIXME: Filter on donations that are viewable (pending & paid)


class MyDonationList(generics.ListCreateAPIView):
    model = Donation
    serializer_class = MyDonationSerializer
    # FIXME: Add permission for OrderOwner

    def get_queryset(self):
        qs = super(MyDonationList, self).get_queryset()
        return qs.filter(user=self.request.user)


class MyDonationDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Donation
    serializer_class = MyDonationSerializer
    # FIXME: Add permission for OrderOwner


