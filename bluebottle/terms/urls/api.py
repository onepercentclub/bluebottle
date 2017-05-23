from django.conf.urls import url

from bluebottle.terms.views import (
    CurrentTermsDetailView, TermsAgreementListView,
    CurrentTermsAgreementDetailView
)

urlpatterns = [
    url(r'^current$',
        CurrentTermsDetailView.as_view(),
        name='current-terms'),
    url(r'^agreements/$',
        TermsAgreementListView.as_view(),
        name='terms-agreement-list'),
    url(r'^agreements/current$',
        CurrentTermsAgreementDetailView.as_view(),
        name='current-terms-agreement'),
]
