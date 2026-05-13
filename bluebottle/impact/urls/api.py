from django.urls import path

from bluebottle.impact.views import (
    ImpactTypeList,
    ImpactGoalList,
    ImpactGoalDetail, ImpactTypeDetail
)

urlpatterns = [
    path('types', ImpactTypeList.as_view(), name='impact-type-list'),
    path(
        'types/<int:pk>',
        ImpactTypeDetail.as_view(),
        name='impact-details'
    ),
    path('goals', ImpactGoalList.as_view(), name='impact-goal-list'),
    path(
        'goals/<int:pk>',
        ImpactGoalDetail.as_view(),
        name='impact-goal-details'
    )
]
