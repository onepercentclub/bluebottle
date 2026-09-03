from django.urls import path

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
    path("", TeamList.as_view(), name="team-list"),

    path("/<int:pk>", TeamDetail.as_view(), name="team-detail"),
    path("/transitions", TeamTransitionList.as_view(), name="team-transition-list"),
    path(
        "/<int:team_id>/members",
        RelatedTeamMembers.as_view(),
        name="related-team-members",
    ),
    path(
        "/<int:pk>/export",
        TeamMemberExportView.as_view(),
        name="team-members-export",
    ),
    path(
        "/activity/<int:activity_id>/",
        RelatedTeamList.as_view(),
        name="related-teams",
    ),

    path("/team-members", TeamMemberList.as_view(), name="team-member-list"),
    path("/team-members/<int:pk>", TeamMemberDetail.as_view(), name="team-member-detail"),
    path("/team-members/transitions", TeamMemberTransitionList.as_view(), name="team-member-transition-list"),

]
