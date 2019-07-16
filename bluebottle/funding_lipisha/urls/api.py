from django.conf.urls import url

from bluebottle.funding_lipisha.views import LipishaPaymentList, LipishaWebHookView


urlpatterns = [
    url(r'^$', LipishaPaymentList.as_view(), name='lipisha-payment-list'),
    url(r'^webhook$', LipishaWebHookView.as_view(), name='lipisha-payment-webhook'),
]
