from django.conf.urls import url

from bluebottle.impact.views import (
    ImpactTypeList,
    ImpactGoalList,
    ImpactGoalDetail
)

urlpatterns = [
    url(r'^types/$', ImpactTypeList.as_view(), name='impact-type-list'),
    url(r'^targets/$', ImpactGoalList.as_view(), name='impact-goal-list'),
    url(
        r'^/targets/(?P<pk>\d+)$',
        ImpactGoalDetail.as_view(),
        name='impact-goal-details'
    )
]
