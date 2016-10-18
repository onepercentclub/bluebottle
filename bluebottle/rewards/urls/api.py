from django.conf.urls import url

from ..views import RewardList, RewardDetail

urlpatterns = [
    url(r'^$', RewardList.as_view(),
        name='reward-list'),
    url(r'^(?P<pk>[\d]+)$', RewardDetail.as_view(),
        name='reward-detail'),

]
