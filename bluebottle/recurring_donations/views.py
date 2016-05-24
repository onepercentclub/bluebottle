from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from bluebottle.recurring_donations.models import MonthlyDonor, \
    MonthlyDonorProject
from bluebottle.recurring_donations.permissions import IsOwner, IsDonor, \
    RecurringDonationsEnabled
from bluebottle.recurring_donations.serializers import \
    MonthlyDonationSerializer, MonthlyDonationProjectSerializer

class MonthlyDonationList(generics.ListCreateAPIView):
    queryset = MonthlyDonor.objects.all()
    permission_classes = (RecurringDonationsEnabled, IsAuthenticated,)
    serializer_class = MonthlyDonationSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        qs = super(MonthlyDonationList, self).get_queryset()
        return qs.filter(user=self.request.user)

    def pre_save(self, obj):
        obj.user = self.request.user


class MonthlyDonationDetail(generics.RetrieveUpdateAPIView):
    queryset = MonthlyDonor.objects.all()
    permission_classes = (RecurringDonationsEnabled, IsOwner,)
    serializer_class = MonthlyDonationSerializer


class MonthlyDonationProjectList(generics.CreateAPIView):
    queryset = MonthlyDonorProject.objects.all()
    permission_classes = (RecurringDonationsEnabled, IsDonor,)
    serializer_class = MonthlyDonationProjectSerializer
    pagination_class = PageNumberPagination


class MonthlyDonationProjectDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = MonthlyDonorProject.objects.all()
    permission_classes = (RecurringDonationsEnabled, IsDonor,)
    serializer_class = MonthlyDonationProjectSerializer
