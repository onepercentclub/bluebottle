from django.conf.urls import url

from bluebottle.time_based.views import (
    TeamTransitionList,
    TeamList,
    TeamDetail,
    RelatedTeamList,
    RelatedTeamMembers,
    TeamMemberExportView, TeamMemberList,
)

urlpatterns = [
    url(r"^$", TeamList.as_view(), name="team-list"),

    url(r"^/(?P<pk>\d+)$", TeamDetail.as_view(), name="team-detail"),
    url(r"^/transitions$", TeamTransitionList.as_view(), name="team-transition-list"),
    url(
        r"^/(?P<team_id>\d+)/members$",
        RelatedTeamMembers.as_view(),
        name="related-team-members",
    ),
    url(
        r"^/(?P<team_id>\d+)/export$",
        TeamMemberExportView.as_view(),
        name="team-members-export",
    ),
    url(
        r"^/activity/(?P<activity_id>\d+)/$",
        RelatedTeamList.as_view(),
        name="related-teams",
    ),

    url(r"^/team-members$", TeamMemberList.as_view(), name="team-member-list"),

]
