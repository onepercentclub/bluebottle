from django.urls import path
from ..views import StatisticList, OldStatisticList, UserStatisticList

urlpatterns = [
    path(
        '', OldStatisticList.as_view(),
        name='statistic-list'
    ),
    path(
        'list', StatisticList.as_view(),
        name='statistics'
    ),
    path(
        'user', UserStatisticList.as_view(),
        name='user-statistics'
    ),
]
