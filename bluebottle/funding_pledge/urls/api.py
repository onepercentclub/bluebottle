from django.conf.urls import url

from bluebottle.funding_pledge.views import PledgePaymentList


urlpatterns = [
    url(r'^$', PledgePaymentList.as_view(), name='pledge-payment-list'),
]
