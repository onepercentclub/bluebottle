from bluebottle.bb_orders.views import ManageOrderList, ManageOrderDetail
from django.conf.urls import url

urlpatterns = [
    # My Orders
    url(r'^my/$', ManageOrderList.as_view(), name='order-manage-list'),
    url(r'^my/(?P<pk>\d+)$', ManageOrderDetail.as_view(), name='order-manage-detail'),
]
