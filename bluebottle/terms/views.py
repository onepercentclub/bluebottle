from bluebottle.terms.models import Terms, TermsAgreement
from bluebottle.terms.serializers import (TermsAgreementSerializer,
                                          TermsSerializer)
from bluebottle.utils.permissions import IsUser
from django.utils.timezone import now
from rest_framework.generics import (ListAPIView, ListCreateAPIView,
                                     RetrieveAPIView, RetrieveDestroyAPIView)
from rest_framework.permissions import IsAuthenticated


class TermsListView(ListAPIView):
    model = Terms
    serializer_class = TermsSerializer
    paginate_by = 1


class TermsDetailView(RetrieveAPIView):
    model = Terms
    serializer_class = TermsSerializer


class CurrentTermsDetailView(TermsDetailView):

    def get_object(self, queryset=None):
        return Terms.get_current()


class TermsAgreementListView(ListCreateAPIView):
    model = TermsAgreement
    serializer_class = TermsAgreementSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        queryset = super(TermsAgreementListView, self).get_queryset()
        return queryset.filter(user=self.request.user)

    def pre_save(self, obj):
        obj.terms = Terms.get_current()
        obj.user = self.request.user


class TermsAgreementDetailView(RetrieveAPIView):
    model = TermsAgreement
    serializer_class = TermsAgreementSerializer
    permission_classes = (IsAuthenticated, IsUser)


class CurrentTermsAgreementDetailView(RetrieveAPIView):
    model = TermsAgreement
    serializer_class = TermsAgreementSerializer
    permission_classes = (IsAuthenticated, )

    def get_object(self, queryset=None):
        return TermsAgreement.get_current(user=self.request.user)
