from django.conf.urls import url

from bluebottle.time_based.views import (
    TeamTransitionList,
    TeamList,
    TeamDetail,
    RelatedTeamList,
)

urlpatterns = [
    url(r"^$", TeamList.as_view(), name="team-list"),
    url(r"^/(?P<pk>\d+)$", TeamDetail.as_view(), name="team-detail"),
    url(r"^/transitions$", TeamTransitionList.as_view(), name="team-transition-list"),
    url(
        r"^/activity/(?P<activity_id>\d+)/$",
        RelatedTeamList.as_view(),
        name="related-teams",
    ),
]
