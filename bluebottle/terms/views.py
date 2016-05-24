from django.http import Http404
from rest_framework.generics import (ListAPIView, RetrieveAPIView,
                                     ListCreateAPIView)
from rest_framework.permissions import IsAuthenticated

from bluebottle.utils.permissions import IsUser
from bluebottle.terms.models import Terms, TermsAgreement
from bluebottle.terms.serializers import (TermsSerializer,
                                          TermsAgreementSerializer)


class TermsListView(ListAPIView):
    queryset = Terms.objects.all()
    serializer_class = TermsSerializer
    paginate_by = 1


class TermsDetailView(RetrieveAPIView):
    queryset = Terms.objects.all()
    serializer_class = TermsSerializer


class CurrentTermsDetailView(TermsDetailView):
    def get_object(self, queryset=None):
        terms = Terms.get_current()
        if terms:
            return terms
        raise Http404


class TermsAgreementListView(ListCreateAPIView):
    queryset = TermsAgreement.objects.all()
    serializer_class = TermsAgreementSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = super(TermsAgreementListView, self).get_queryset()
        return queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(terms=Terms.get_current(), user=self.request.user)


class TermsAgreementDetailView(RetrieveAPIView):
    queryset = TermsAgreement.objects.all()
    serializer_class = TermsAgreementSerializer
    permission_classes = (IsAuthenticated, IsUser)


class CurrentTermsAgreementDetailView(RetrieveAPIView):
    queryset = TermsAgreement.objects.all()
    serializer_class = TermsAgreementSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self, queryset=None):
        return TermsAgreement.get_current(user=self.request.user)
