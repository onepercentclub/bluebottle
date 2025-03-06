from django.urls import re_path

from bluebottle.time_based.views import (
    TeamTransitionList,
    TeamList,
    TeamDetail,
    RelatedTeamList,
    RelatedTeamMembers,
    TeamMemberExportView,
    TeamMemberList,
    TeamMemberDetail, TeamMemberTransitionList
)

urlpatterns = [
    re_path(r"^$", TeamList.as_view(), name="team-list"),

    re_path(r"^/(?P<pk>\d+)$", TeamDetail.as_view(), name="team-detail"),
    re_path(r"^/transitions$", TeamTransitionList.as_view(), name="team-transition-list"),
    re_path(
        r"^/(?P<team_id>\d+)/members$",
        RelatedTeamMembers.as_view(),
        name="related-team-members",
    ),
    re_path(
        r"^/(?P<pk>\d+)/export$",
        TeamMemberExportView.as_view(),
        name="team-members-export",
    ),
    re_path(
        r"^/activity/(?P<activity_id>\d+)/$",
        RelatedTeamList.as_view(),
        name="related-teams",
    ),

    re_path(r"^/team-members$", TeamMemberList.as_view(), name="team-member-list"),
    re_path(r"^/team-members/(?P<pk>\d+)$", TeamMemberDetail.as_view(), name="team-member-detail"),
    re_path(r"^/team-members/transitions$", TeamMemberTransitionList.as_view(), name="team-member-transition-list"),

]
