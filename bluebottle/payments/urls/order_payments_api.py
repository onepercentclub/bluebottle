from django.conf.urls import url

from ..views import ManageOrderPaymentList, ManageOrderPaymentDetail

urlpatterns = [
    url(r'^my/$', ManageOrderPaymentList.as_view(),
        name='manage-order-payment-list'),
    url(r'^my/(?P<pk>\d+)$', ManageOrderPaymentDetail.as_view(),
        name='manage-order-payment-detail'),
]
