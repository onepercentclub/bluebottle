from django.urls import re_path

from bluebottle.terms.views import (
    CurrentTermsDetailView, TermsAgreementListView,
    CurrentTermsAgreementDetailView
)

urlpatterns = [
    re_path(
        r'^current$',
        CurrentTermsDetailView.as_view(),
        name='current-terms'
    ),
    re_path(
        r'^agreements/$',
        TermsAgreementListView.as_view(),
        name='terms-agreement-list'
    ),
    re_path(
        r'^agreements/current$',
        CurrentTermsAgreementDetailView.as_view(),
        name='current-terms-agreement'
    ),
]
