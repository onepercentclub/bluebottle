from django.conf.urls import url

from .views import ProjectPayoutDetail, PaymentMethodList


urlpatterns = [
    url(r'^projects/(?P<pk>[\d]+)$',
        ProjectPayoutDetail.as_view(),
        name='project-payout-detail'),
    url(r'^methods/$',
        PaymentMethodList.as_view(),
        name='payout-method-list'),
]
