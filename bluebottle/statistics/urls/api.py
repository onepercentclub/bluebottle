from django.conf.urls import url
from ..views import StatisticList

urlpatterns = [
    url(
        r'^$', StatisticList.as_view(),
        name='statistic-list'
    ),
]
