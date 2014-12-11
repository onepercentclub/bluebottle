from bluebottle.utils.permissions import IsUser
from django.utils.timezone import now
from bluebottle.terms.models import Terms, TermsAgreement
from bluebottle.terms.serializers import TermsSerializer, TermsAgreementSerializer
from rest_framework.generics import ListAPIView, RetrieveAPIView, RetrieveDestroyAPIView
from rest_framework.permissions import IsAuthenticated


class TermsListView(ListAPIView):
    model = Terms
    serializer_class = TermsSerializer


class TermsDetailView(RetrieveAPIView):
    model = Terms
    serializer_class = TermsSerializer


class CurrentTermsDetailView(TermsDetailView):

    def get_object(self, queryset=None):
        return Terms.objects.filter(date__lte=now()).order_by('-date')[0]


class TermsAgreementListView(ListAPIView):
    model = TermsAgreement
    serializer_class = TermsAgreementSerializer
    permission_classes = (IsAuthenticated, IsUser)

    def get_queryset(self):
        queryset = super(TermsAgreementListView, self).get_queryset()
        return queryset.filter(user=self.request.user)


class TermsAgreementDetailView(RetrieveDestroyAPIView):
    model = TermsAgreement
    serializer_class = TermsAgreementSerializer
    permission_classes = (IsAuthenticated, IsUser)
