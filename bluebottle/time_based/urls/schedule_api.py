from django.conf.urls import url

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
    url(r'^$',
        ScheduleActivityListView.as_view(),
        name='schedule-list'),
    url(r'^/(?P<pk>\d+)$',
        ScheduleActivityDetailView.as_view(),
        name='schedule-detail'),
    url(r'^/transitions$',
        ScheduleTransitionList.as_view(),
        name='schedule-transition-list'),

    url(r'^/(?P<activity_id>\d+)/registrations/$',
        ScheduleRelatedRegistrationList.as_view(),
        name='related-schedule-registrations'),
    url(r'^/registrations/$',
        ScheduleRegistrationList.as_view(),
        name='schedule-registration-list'),
    url(r'^/registrations/transitions$',
        ScheduleRegistrationTransitionList.as_view(),
        name='schedule-registration-transitions'),
    url(r'^/registrations/(?P<pk>\d+)$',
        ScheduleRegistrationDetail.as_view(),
        name='schedule-registration-detail'),
    url(r'^/registrations/(?P<pk>\d+)/document$',
        ScheduleRegistrationDocumentDetail.as_view(),
        name='schedule-registration-document'),

    url(r'^/(?P<activity_id>\d+)/team-registrations/$',
        TeamScheduleRelatedRegistrationList.as_view(),
        name='related-team-schedule-registrations'),
    url(r'^/team-registrations/$',
        TeamScheduleRegistrationList.as_view(),
        name='team-schedule-registration-list'),
    url(r'^/team-registrations/(?P<pk>\d+)$',
        TeamScheduleRegistrationDetail.as_view(),
        name='team-schedule-registration-detail'),
    url(r'^/team-registrations/transitions$',
        TeamScheduleRegistrationTransitionList.as_view(),
        name='team-schedule-registration-transitions'),

    url(r'^/(?P<activity_id>\d+)/participants$',
        ScheduleRelatedParticipantList.as_view(),
        name='schedule-participants'),
    url(r'^/participants/transitions$',
        ScheduleParticipantTransitionList.as_view(),
        name='schedule-participant-transitions'),
    url(r'^/participants/(?P<pk>\d+)$',
        ScheduleParticipantDetail.as_view(),
        name="schedule-participant-detail"),

    url(r'^/(?P<activity_id>\d+)/team-participants$',
        TeamScheduleRelatedParticipantList.as_view(),
        name='team-schedule-participants'),
    url(r'^/team-participants/(?P<pk>\d+)$',
        TeamScheduleParticipantDetail.as_view(),
        name="team-schedule-participant-detail"),
    url(r'^/team-participants/transitions$',
        TeamScheduleParticipantTransitionList.as_view(),
        name='team-schedule-participant-transitions'),

    url(r"/slots$", ScheduleSlotListView.as_view(), name="schedule-slot-list"),
    url(
        r"^/slots/(?P<pk>\d+)$",
        ScheduleSlotDetailView.as_view(),
        name="schedule-slot-detail",
    ),
    url(
        r"^/slots/ical/(?P<pk>\d+)$",
        ScheduleSlotSlotIcalView.as_view(),
        name="schedule-slot-ical",
    ),

    url(r"/team-slots$", TeamScheduleSlotListView.as_view(), name="team-schedule-slot-list"),
    url(
        r"^/team-slots/(?P<pk>\d+)$",
        TeamScheduleSlotDetailView.as_view(),
        name="team-schedule-slot-detail",
    ),
    url(
        r"^/team-slots/ical/(?P<pk>\d+)$",
        TeamScheduleSlotSlotIcalView.as_view(),
        name="team-schedule-slot-ical",
    ),

    url(r'^/team-slots/(?P<slot_id>\d+)/team-participants$',
        TeamSlotScheduleRelatedParticipantList.as_view(),
        name='slot-schedule-participants'),

    url(
        r"^/export/(?P<pk>[\d]+)$",
        ScheduleParticipantExportView.as_view(),
        name="schedule-participant-export",
    ),
    url(
        r"^/teams/export/(?P<pk>[\d]+)$",
        TeamScheduleParticipantExportView.as_view(),
        name="team-schedule-participant-export",
    ),
]
