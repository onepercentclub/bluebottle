from django.conf.urls import url
from ..views import StatisticList, OldStatisticList

urlpatterns = [
    url(
        r'^$', OldStatisticList.as_view(),
        name='statistic-list'
    ),
    url(
        r'^list$', StatisticList.as_view(),
        name='statistics'
    ),
]
