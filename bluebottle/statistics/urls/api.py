from django.urls import re_path
from ..views import StatisticList, OldStatisticList, UserStatisticList

urlpatterns = [
    re_path(
        r'^$', OldStatisticList.as_view(),
        name='statistic-list'
    ),
    re_path(
        r'^list$', StatisticList.as_view(),
        name='statistics'
    ),
    re_path(
        r'^user$', UserStatisticList.as_view(),
        name='user-statistics'
    ),
]
