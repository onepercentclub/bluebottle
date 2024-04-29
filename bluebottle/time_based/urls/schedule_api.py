from django.conf.urls import url

from bluebottle.time_based.views import (
    ScheduleTransitionList,
    ScheduleActivityListView,
    ScheduleActivityDetailView,
    ScheduleRelatedRegistrationList,
    ScheduleRegistrationList,
    ScheduleRegistrationTransitionList,
    ScheduleRegistrationDetail,
    ScheduleRegistrationDocumentDetail,
    ScheduleParticipantTransitionList,
    ScheduleParticipantExportView,
    ScheduleRelatedParticipantList,
    ScheduleParticipantDetail,
    ScheduleSlotListView,
    ScheduleSlotDetailView,
)

urlpatterns = [
    url(r"^$", ScheduleActivityListView.as_view(), name="schedule-list"),
    url(
        r"^/(?P<pk>\d+)$", ScheduleActivityDetailView.as_view(), name="schedule-detail"
    ),
    url(
        r"^/transitions$",
        ScheduleTransitionList.as_view(),
        name="schedule-transition-list",
    ),
    url(
        r"^/(?P<activity_id>\d+)/registrations/$",
        ScheduleRelatedRegistrationList.as_view(),
        name="related-schedule-registrations",
    ),
    url(
        r"^/registrations/$",
        ScheduleRegistrationList.as_view(),
        name="schedule-registration-list",
    ),
    url(
        r"^/registrations/transitions$",
        ScheduleRegistrationTransitionList.as_view(),
        name="schedule-registration-transitions",
    ),
    url(
        r"^/registrations/(?P<pk>\d+)$",
        ScheduleRegistrationDetail.as_view(),
        name="schedule-registration-detail",
    ),
    url(
        r"^/registrations/(?P<pk>\d+)/document$",
        ScheduleRegistrationDocumentDetail.as_view(),
        name="schedule-registration-document",
    ),
    url(
        r"^/(?P<activity_id>\d+)/participants$",
        ScheduleRelatedParticipantList.as_view(),
        name="schedule-participants",
    ),
    url(
        r"^/participants/transitions$",
        ScheduleParticipantTransitionList.as_view(),
        name="schedule-participant-transitions",
    ),
    url(
        r"^/participants/(?P<pk>\d+)$",
        ScheduleParticipantDetail.as_view(),
        name="schedule-participant-detail",
    ),
    url(r"/slots$", ScheduleSlotListView.as_view(), name="schedule-slot-list"),
    url(
        r"^/slots/(?P<pk>\d+)$",
        ScheduleSlotDetailView.as_view(),
        name="schedule-slot-detail",
    ),
    url(
        r"^/export/(?P<pk>[\d]+)$",
        ScheduleParticipantExportView.as_view(),
        name="schedule-participant-export",
    ),
]
