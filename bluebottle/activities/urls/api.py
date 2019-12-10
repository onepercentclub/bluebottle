from django.conf.urls import url

from bluebottle.activities.views import (
    ActivityList, ActivityDetail, ActivityReviewTransitionList,
    ContributionList, RelatedActivityImageList,
    RelatedActivityImageContent,
)

urlpatterns = [
    url(
        r'^/review-transitions$',
        ActivityReviewTransitionList.as_view(),
        name='activity-review-transition-list'),
    url(r'^$',
        ActivityList.as_view(),
        name='activity-list'),
    url(r'^/contributions$',
        ContributionList.as_view(),
        name='contribution-list'),

    url(r'^/(?P<pk>\d+)$',
        ActivityDetail.as_view(),
        name='activity-detail'),

    url(r'^/related-images$',
        RelatedActivityImageList.as_view(),
        name='related-activity-image-list'),
    url(
        r'^/(?P<pk>\d+)/related-image/(?P<size>\d+(x\d+)?)$',
        RelatedActivityImageContent.as_view(),
        name='related-activity-image-content'
    ),
]
