from django.conf.urls import url

from bluebottle.activities.views import (
    ActivityList, ActivityDetail, ActivityReviewTransitionList
)

urlpatterns = [
    url(
        r'^/review-transitions$',
        ActivityReviewTransitionList.as_view(),
        name='activity-review-transition-list'),
    url(r'^$',
        ActivityList.as_view(),
        name='activity-list'),
    url(r'^/(?P<pk>\d+)$',
        ActivityDetail.as_view(),
        name='activity-detail'),
]
