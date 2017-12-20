from django.conf.urls import url

from bluebottle.payments_lipisha.views import PaymentUpdateView


urlpatterns = [
    url(r'^update/$',
        PaymentUpdateView.as_view(),
        name='lipisha-update-payment'),
]
