import logging
from bluebottle.bb_donations.serializers import MyDonationSerializer
from .serializers import DonationSerializer
from django.contrib.auth.models import AnonymousUser
from rest_framework import generics
from bluebottle.utils.utils import get_project_model, get_model_class

PROJECT_MODEL = get_project_model()
DONATION_MODEL = get_model_class('DONATIONS_DONATION_MODEL')

logger = logging.getLogger(__name__)


class DonationList(generics.ListAPIView):
    model = DONATION_MODEL
    serializer_class = DonationSerializer
    # FIXME: Filter on donations that are viewable (pending & paid)


class DonationDetail(generics.RetrieveAPIView):
    model = DONATION_MODEL
    serializer_class = DonationSerializer
    # FIXME: Filter on donations that are viewable (pending & paid)


class MyDonationList(generics.ListCreateAPIView):
    model = DONATION_MODEL
    serializer_class = MyDonationSerializer
    # FIXME: Add permission for OrderOwner

    def get_queryset(self):
        qs = super(MyDonationList, self).get_queryset()
        return qs.filter(user=self.request.user)


class MyDonationDetail(generics.RetrieveUpdateDestroyAPIView):
    model = DONATION_MODEL
    serializer_class = MyDonationSerializer
    # FIXME: Add permission for OrderOwner


