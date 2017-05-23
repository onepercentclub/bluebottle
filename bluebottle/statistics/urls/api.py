from django.conf.urls import url
from ..views import StatisticDetail

urlpatterns = [
    url(r'^current$', StatisticDetail.as_view(),
        name='stats'),
]
