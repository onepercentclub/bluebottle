from django.urls import re_path

from bluebottle.activity_links.views import (
    LinkedActivityImage, CollectLinkDetail, DateLinkDetail, DeadlineLinkDetail,
    DeedLinkDetail, FundingLinkDetail, GrantApplicationLinkDetail, PeriodicLinkDetail,
    ScheduleLinkDetail,
)

app_name = 'activity_links'

urlpatterns = [
    re_path(r'^image/(?P<pk>\d+)/(?P<size>\d+(x\d+)?)$', LinkedActivityImage.as_view(), name='image'),
    re_path(r'^deed-activity-link/(?P<pk>\d+)$', DeedLinkDetail.as_view(), name='deed-activity-link'),
    re_path(r'^collect-activity-link/(?P<pk>\d+)$', CollectLinkDetail.as_view(), name='collect-activity-link'),
    re_path(r'^funding-activity-link/(?P<pk>\d+)$', FundingLinkDetail.as_view(), name='funding-activity-link'),
    re_path(
        r'^grant-application-activity-link/(?P<pk>\d+)$',
        GrantApplicationLinkDetail.as_view(),
        name='grant-application-activity-link'
    ),
    re_path(r'^deadline-activity-link/(?P<pk>\d+)$', DeadlineLinkDetail.as_view(), name='deadline-activity-link'),
    re_path(r'^date-activity-link/(?P<pk>\d+)$', DateLinkDetail.as_view(), name='date-activity-link'),
    re_path(r'^periodic-activity-link/(?P<pk>\d+)$', PeriodicLinkDetail.as_view(), name='periodic-activity-link'),
    re_path(r'^schedule-activity-link/(?P<pk>\d+)$', ScheduleLinkDetail.as_view(), name='schedule-activity-link'),
]
