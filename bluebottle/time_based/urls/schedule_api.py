from django.urls import re_path

from bluebottle.time_based.views import (
    ScheduleTransitionList,
    ScheduleActivityListView, ScheduleActivityDetailView,
    ScheduleRelatedRegistrationList, ScheduleRegistrationList, ScheduleRegistrationTransitionList,
    ScheduleRegistrationDetail,
    ScheduleRegistrationDocumentDetail,
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
    TeamScheduleRegistrationDocumentDetail,

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
    re_path(r'^$',
        ScheduleActivityListView.as_view(),
        name='schedule-list'),
    re_path(r'^/(?P<pk>\d+)$',
        ScheduleActivityDetailView.as_view(),
        name='schedule-detail'),
    re_path(r'^/transitions$',
        ScheduleTransitionList.as_view(),
        name='schedule-transition-list'),

    re_path(r'^/(?P<activity_id>\d+)/registrations/$',
        ScheduleRelatedRegistrationList.as_view(),
        name='related-schedule-registrations'),
    re_path(r'^/registrations/$',
        ScheduleRegistrationList.as_view(),
        name='schedule-registration-list'),
    re_path(r'^/registrations/transitions$',
        ScheduleRegistrationTransitionList.as_view(),
        name='schedule-registration-transitions'),
    re_path(r'^/registrations/(?P<pk>\d+)$',
        ScheduleRegistrationDetail.as_view(),
        name='schedule-registration-detail'),
    re_path(r'^/registrations/(?P<pk>\d+)/document$',
        ScheduleRegistrationDocumentDetail.as_view(),
        name='schedule-registration-document'),

    re_path(r'^/(?P<activity_id>\d+)/team-registrations/$',
        TeamScheduleRelatedRegistrationList.as_view(),
        name='related-team-schedule-registrations'),
    re_path(r'^/team-registrations/$',
        TeamScheduleRegistrationList.as_view(),
        name='team-schedule-registration-list'),
    re_path(r'^/team-registrations/(?P<pk>\d+)$',
        TeamScheduleRegistrationDetail.as_view(),
        name='team-schedule-registration-detail'),
    re_path(r'^/team-registrations/transitions$',
        TeamScheduleRegistrationTransitionList.as_view(),
        name="team-schedule-registration-transitions"),
    re_path(
        r"^/team-registrations/(?P<pk>\d+)/document$",
        TeamScheduleRegistrationDocumentDetail.as_view(),
        name="team-schedule-registration-document",
    ),
    re_path(
        r"^/(?P<activity_id>\d+)/participants$",
        ScheduleRelatedParticipantList.as_view(),
        name='schedule-participants'),
    re_path(r'^/participants/transitions$',
        ScheduleParticipantTransitionList.as_view(),
        name='schedule-participant-transitions'),
    re_path(r'^/participants/(?P<pk>\d+)$',
        ScheduleParticipantDetail.as_view(),
        name="schedule-participant-detail"),

    re_path(r'^/(?P<activity_id>\d+)/team-participants$',
        TeamScheduleRelatedParticipantList.as_view(),
        name='team-schedule-participants'),
    re_path(r'^/team-participants/(?P<pk>\d+)$',
        TeamScheduleParticipantDetail.as_view(),
        name="team-schedule-participant-detail"),
    re_path(r'^/team-participants/transitions$',
        TeamScheduleParticipantTransitionList.as_view(),
        name='team-schedule-participant-transitions'),

    re_path(r"/slots$", ScheduleSlotListView.as_view(), name="schedule-slot-list"),
    re_path(
        r"^/slots/(?P<pk>\d+)$",
        ScheduleSlotDetailView.as_view(),
        name="schedule-slot-detail",
    ),
    re_path(
        r"^/slots/ical/(?P<pk>\d+)$",
        ScheduleSlotSlotIcalView.as_view(),
        name="schedule-slot-ical",
    ),

    re_path(r"/team-slots$", TeamScheduleSlotListView.as_view(), name="team-schedule-slot-list"),
    re_path(
        r"^/team-slots/(?P<pk>\d+)$",
        TeamScheduleSlotDetailView.as_view(),
        name="team-schedule-slot-detail",
    ),
    re_path(
        r"^/team-slots/ical/(?P<pk>\d+)$",
        TeamScheduleSlotSlotIcalView.as_view(),
        name="team-schedule-slot-ical",
    ),

    re_path(r'^/team-slots/(?P<slot_id>\d+)/team-participants$',
        TeamSlotScheduleRelatedParticipantList.as_view(),
        name='slot-schedule-participants'),

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
