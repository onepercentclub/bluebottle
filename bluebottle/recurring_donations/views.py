from bluebottle.recurring_donations.models import MonthlyDonor, MonthlyDonorProject
from bluebottle.recurring_donations.permissions import IsOwner, IsDonor, RecurringDonationsEnabled
from bluebottle.recurring_donations.serializers import MonthlyDonationSerializer, MonthlyDonationProjectSerializer
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated


class MonthlyDonationList(generics.ListCreateAPIView):
    model = MonthlyDonor
    permission_classes = (RecurringDonationsEnabled, IsAuthenticated, )
    serializer_class = MonthlyDonationSerializer
    paginate_by = 10

    def get_queryset(self):
        qs = super(MonthlyDonationList, self).get_queryset()
        return qs.filter(user=self.request.user)

    def pre_save(self, obj):
        obj.user = self.request.user

class MonthlyDonationDetail(generics.RetrieveUpdateAPIView):
    model = MonthlyDonor
    permission_classes = (RecurringDonationsEnabled, IsOwner, )
    serializer_class = MonthlyDonationSerializer


class MonthlyDonationProjectList(generics.CreateAPIView):
    model = MonthlyDonorProject
    permission_classes = (RecurringDonationsEnabled, IsDonor, )
    serializer_class = MonthlyDonationProjectSerializer
    paginate_by = 10


class MonthlyDonationProjectDetail(generics.RetrieveUpdateDestroyAPIView):
    model = MonthlyDonorProject
    permission_classes = (RecurringDonationsEnabled, IsDonor, )
    serializer_class = MonthlyDonationProjectSerializer

