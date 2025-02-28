from django.urls import re_path

from bluebottle.impact.views import (
    ImpactTypeList,
    ImpactGoalList,
    ImpactGoalDetail, ImpactTypeDetail
)

urlpatterns = [
    re_path(r'^types$', ImpactTypeList.as_view(), name='impact-type-list'),
    re_path(
        r'^types/(?P<pk>\d+)$',
        ImpactTypeDetail.as_view(),
        name='impact-details'
    ),
    re_path(r'^goals$', ImpactGoalList.as_view(), name='impact-goal-list'),
    re_path(
        r'^goals/(?P<pk>\d+)$',
        ImpactGoalDetail.as_view(),
        name='impact-goal-details'
    )
]
