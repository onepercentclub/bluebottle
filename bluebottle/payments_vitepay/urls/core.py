from django.conf.urls import url

from bluebottle.funding_vitepay.views import VitepayWebhookView


urlpatterns = [
    url(r'^status_update/$',
        VitepayWebhookView.as_view(),
        name='vitepay-status-update')
]
