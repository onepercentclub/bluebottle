from bluebottle.time_based.views.participants import ScheduleParticipantList
from django.urls import path
from django.urls import re_path

from bluebottle.time_based.views import (
    ScheduleTransitionList,
    ScheduleActivityListView, ScheduleActivityDetailView,
    ScheduleRelatedRegistrationList, ScheduleRegistrationList, ScheduleRegistrationTransitionList,
    ScheduleRegistrationDetail,
    ScheduleParticipantTransitionList,
    ScheduleParticipantExportView,
    TeamScheduleParticipantExportView,
    ScheduleRelatedParticipantList,
    ScheduleParticipantDetail,

    ScheduleSlotListView,
    ScheduleSlotDetailView,
    TeamScheduleSlotListView,
    TeamScheduleSlotDetailView,

    TeamScheduleRegistrationList,
    TeamScheduleRegistrationDetail,
    TeamScheduleRelatedRegistrationList,
    TeamScheduleRegistrationTransitionList,

    TeamScheduleParticipantDetail,
    TeamScheduleRelatedParticipantList,
    TeamScheduleParticipantTransitionList,
    TeamSlotScheduleRelatedParticipantList
)
from bluebottle.time_based.views.slots import (
    ScheduleSlotSlotIcalView,
    TeamScheduleSlotSlotIcalView,
)

urlpatterns = [
    path(
        '',
        ScheduleActivityListView.as_view(),
        name='schedule-list'
    ),
    path(
        '/<int:pk>',
        ScheduleActivityDetailView.as_view(),
        name='schedule-detail'
    ),
    path(
        '/transitions',
        ScheduleTransitionList.as_view(),
        name='schedule-transition-list'
    ),

    path(
        '/<int:activity_id>/registrations/',
        ScheduleRelatedRegistrationList.as_view(),
        name='related-schedule-registrations'
    ),
    path(
        '/registrations/',
        ScheduleRegistrationList.as_view(),
        name='schedule-registration-list'
    ),
    path(
        '/registrations/transitions',
        ScheduleRegistrationTransitionList.as_view(),
        name='schedule-registration-transitions'
    ),
    path(
        '/registrations/<int:pk>',
        ScheduleRegistrationDetail.as_view(),
        name='schedule-registration-detail'
    ),
    path(
        '/<int:activity_id>/team-registrations/',
        TeamScheduleRelatedRegistrationList.as_view(),
        name='related-team-schedule-registrations'
    ),
    path(
        '/team-registrations/',
        TeamScheduleRegistrationList.as_view(),
        name='team-schedule-registration-list'
    ),
    path(
        '/team-registrations/<int:pk>',
        TeamScheduleRegistrationDetail.as_view(),
        name='team-schedule-registration-detail'
    ),
    path(
        '/team-registrations/transitions',
        TeamScheduleRegistrationTransitionList.as_view(),
        name="team-schedule-registration-transitions"
    ),
    path(
        "/<int:activity_id>/participants",
        ScheduleRelatedParticipantList.as_view(),
        name='schedule-participants'
    ),
    path(
        '/participants/transitions',
        ScheduleParticipantTransitionList.as_view(),
        name='schedule-participant-transitions'
    ),
    path(
        '/participants/<int:pk>',
        ScheduleParticipantDetail.as_view(),
        name="schedule-participant-detail"
    ),
    path(
        '/participants',
        ScheduleParticipantList.as_view(),
        name='schedule-participant-create'
    ),

    path(
        '/<int:activity_id>/team-participants',
        TeamScheduleRelatedParticipantList.as_view(),
        name='team-schedule-participants'
    ),
    path(
        '/team-participants/<int:pk>',
        TeamScheduleParticipantDetail.as_view(),
        name="team-schedule-participant-detail"
    ),
    path(
        '/team-participants/transitions',
        TeamScheduleParticipantTransitionList.as_view(),
        name='team-schedule-participant-transitions'
    ),

    path("/slots", ScheduleSlotListView.as_view(), name="schedule-slot-list"),
    path(
        "/slots/<int:pk>",
        ScheduleSlotDetailView.as_view(),
        name="schedule-slot-detail",
    ),
    path(
        "/slots/ical/<int:pk>",
        ScheduleSlotSlotIcalView.as_view(),
        name="schedule-slot-ical",
    ),

    path("/team-slots", TeamScheduleSlotListView.as_view(), name="team-schedule-slot-list"),
    path(
        "/team-slots/<int:pk>",
        TeamScheduleSlotDetailView.as_view(),
        name="team-schedule-slot-detail",
    ),
    path(
        "/team-slots/ical/<int:pk>",
        TeamScheduleSlotSlotIcalView.as_view(),
        name="team-schedule-slot-ical",
    ),

    path(
        '/team-slots/<int:slot_id>/team-participants',
        TeamSlotScheduleRelatedParticipantList.as_view(),
        name='slot-schedule-participants'
    ),

    re_path(
        r"^/export/(?P<pk>[\d]+)$",
        ScheduleParticipantExportView.as_view(),
        name="schedule-participant-export",
    ),
    re_path(
        r"^/teams/export/(?P<pk>[\d]+)$",
        TeamScheduleParticipantExportView.as_view(),
        name="team-schedule-participant-export",
    ),
]
