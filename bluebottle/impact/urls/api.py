from django.conf.urls import url

from bluebottle.impact.views import (
    ImpactTypeList,
    ImpactGoalList,
    ImpactGoalDetail, ImpactTypeDetail
)

urlpatterns = [
    url(r'^types$', ImpactTypeList.as_view(), name='impact-type-list'),
    url(
        r'^types/(?P<pk>\d+)$',
        ImpactTypeDetail.as_view(),
        name='impact-details'
    ),
    url(r'^goals$', ImpactGoalList.as_view(), name='impact-goal-list'),
    url(
        r'^goals/(?P<pk>\d+)$',
        ImpactGoalDetail.as_view(),
        name='impact-goal-details'
    )
]
