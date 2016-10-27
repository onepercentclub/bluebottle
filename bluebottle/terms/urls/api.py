from bluebottle.terms.views import TermsListView, CurrentTermsDetailView, \
    TermsDetailView, TermsAgreementListView, \
    TermsAgreementDetailView, CurrentTermsAgreementDetailView
from django.conf.urls import url

urlpatterns = [
    url(r'^current$', CurrentTermsDetailView.as_view(), name='current-terms'),

    url(r'^agreements/$', TermsAgreementListView.as_view(),
        name='terms-agreement-list'),
    url(r'^agreements/current$', CurrentTermsAgreementDetailView.as_view(),
        name='current-terms-agreement'),
]
