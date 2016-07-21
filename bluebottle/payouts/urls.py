from django.conf.urls import patterns, url

from .views import PayoutList, PayoutDetail

urlpatterns = patterns(
    '',
    url(r'^$', PayoutList.as_view(), name='payout_list'),
    url(r'^(?P<pk>[\d]+)$', PayoutDetail.as_view(), name='payout_detail'),
)
