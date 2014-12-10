from bluebottle.terms.views import TermsListView, CurrentTermsDetailView, TermsDetailView, TermsAgreementListView, \
    TermsAgreementDetailView
from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^$', TermsListView.as_view(), name='terms-list'),
    url(r'^current$', CurrentTermsDetailView.as_view(), name='terms-current'),
    url(r'^(?P<pk>\d+)$', TermsDetailView.as_view(), name='terms-detail'),

    url(r'^agreements/$', TermsAgreementListView.as_view(), name='terms-list'),
    url(r'^agreements/(?P<pk>\d+)$', TermsAgreementDetailView.as_view(), name='terms-detail'),


)
