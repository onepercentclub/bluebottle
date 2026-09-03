from django.urls import path

from bluebottle.terms.views import (
    CurrentTermsDetailView, TermsAgreementListView,
    CurrentTermsAgreementDetailView
)

urlpatterns = [
    path(
        'current',
        CurrentTermsDetailView.as_view(),
        name='current-terms'
    ),
    path(
        'agreements/',
        TermsAgreementListView.as_view(),
        name='terms-agreement-list'
    ),
    path(
        'agreements/current',
        CurrentTermsAgreementDetailView.as_view(),
        name='current-terms-agreement'
    ),
]
