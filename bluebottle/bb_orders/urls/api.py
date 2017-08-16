from bluebottle.bb_orders.views import ManageOrderList, ManageOrderDetail
from django.conf.urls import url
from ..views import OrderList, OrderDetail

urlpatterns = [
    # Orders
    url(r'^$', OrderList.as_view(), name='order-list'),
    url(r'^(?P<pk>\d+)$', OrderDetail.as_view(), name='order-detail'),

    # My Orders
    url(r'^my/$', ManageOrderList.as_view(), name='order-manage-list'),
    url(r'^my/(?P<pk>\d+)$', ManageOrderDetail.as_view(), name='order-manage-detail'),
]
