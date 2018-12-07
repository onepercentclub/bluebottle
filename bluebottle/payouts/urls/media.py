from django.conf.urls import url

from bluebottle.payouts.views import PayoutDocumentFileView


urlpatterns = [
    url(r'^payouts/documents/(?P<pk>\d+)',
        PayoutDocumentFileView.as_view(),
        name='payout-document-file'),
]
