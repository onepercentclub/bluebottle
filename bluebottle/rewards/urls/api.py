from django.conf.urls import patterns, url

from ..views import RewardList, RewardDetail

urlpatterns = patterns(
    '',
    url(r'^$', RewardList.as_view(),
        name='reward-list'),
    url(r'^(?P<pk>[\d]+)$', RewardDetail.as_view(),
        name='reward-detail'),

)
