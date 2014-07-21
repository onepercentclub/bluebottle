from django.conf.urls import patterns, include, url
from ..views import OrderList, OrderDetail

urlpatterns = patterns('',
    # Orders
    url(r'^$', OrderList.as_view(), name='order-list'),
    url(r'^(?P<pk>\d+)$', OrderDetail.as_view(), name='order-detail'),

)
