from django.urls import include, re_path

from bluebottle.time_based.views import (
    DateActivityDetailView,
    DateActivityListView,
    DateActivityRelatedParticipantList,
    DateParticipantDetail,
    DateParticipantDocumentDetail,
    DateParticipantList,
    DateParticipantTransitionList,
    DateTransitionList,
    TimeContributionDetail,
    DateSlotDetailView,
    DateSlotListView,
    SlotParticipantListView,
    SlotParticipantDetailView,
    SlotParticipantTransitionList,
    DateActivityIcalView,
    ActivitySlotIcalView,
    DateParticipantExportView,
    SlotRelatedParticipantList,
    SkillList,
    SkillDetail,
    RelatedSlotParticipantListView,
    DateSlotTransitionList,
    SlotParticipantExportView, PeriodActivityDetailView
)

urlpatterns = [
    re_path(r'^/date$',
        DateActivityListView.as_view(),
        name='date-list'),

    re_path(r'^/date/(?P<pk>\d+)$',
        DateActivityDetailView.as_view(),
        name='date-detail'),

    re_path(r'^/date/(?P<activity_id>\d+)/participants$',
        DateActivityRelatedParticipantList.as_view(),
        name='date-participants'),

    re_path(r'^/date/slots/(?P<slot_id>\d+)/participants$',
        SlotRelatedParticipantList.as_view(),
        name='slot-participants'),

    re_path(r'^/date/slots$',
        DateSlotListView.as_view(),
        name='date-slot-list'),

    re_path(r'^/date/(?P<pk>\d+)/(?P<related_field>\w+)$',
        DateSlotListView.as_view(),
        name='date-slots'),

    re_path(r'^/date/slots/(?P<pk>\d+)$',
        DateSlotDetailView.as_view(),
        name='date-slot-detail'),

    re_path(r'^/date/ical/(?P<pk>\d+)/(?P<user_id>\d+)$',
        DateActivityIcalView.as_view(),
        name='date-ical'),

    re_path(r'^/slot/ical/(?P<pk>\d+)$',
        ActivitySlotIcalView.as_view(),
        name='slot-ical'),

    re_path(r'^/date/transitions$',
        DateTransitionList.as_view(),
        name='date-transition-list'),

    re_path(r'^/slot/transitions$',
        DateSlotTransitionList.as_view(),
        name='slot-transition-list'),

    re_path(r'^/participants/date$',
        DateParticipantList.as_view(),
        name='date-participant-list'),
    re_path(r'^/participants/date/(?P<pk>\d+)$',
        DateParticipantDetail.as_view(),
        name='date-participant-detail'),
    re_path(r'^/participants/date/transitions$',
        DateParticipantTransitionList.as_view(),
        name='date-participant-transition-list'),

    re_path(r'^/participants/date/(?P<pk>\d+)/document$',
        DateParticipantDocumentDetail.as_view(),
        name='date-participant-document'),

    re_path(r'^/slot-participants$',
        SlotParticipantListView.as_view(),
        name='slot-participant-list'),

    re_path(r'^/participants/date/(?P<participant_id>\d+)/slot-participants$',
        RelatedSlotParticipantListView.as_view(),
        name='related-slot-participant-list'),

    re_path(r'^/slot-participants/(?P<pk>\d+)$',
        SlotParticipantDetailView.as_view(),
        name='slot-participant-detail'),
    re_path(r'^/slot-participants/transitions$',
        SlotParticipantTransitionList.as_view(),
        name='slot-participant-transition-list'),

    re_path(r'^/contributions/time/(?P<pk>\d+)$',
        TimeContributionDetail.as_view(),
        name='time-contribution-detail'),

    re_path(r'^/date/export/(?P<pk>[\d]+)$',
        DateParticipantExportView.as_view(),
        name='date-participant-export'),

    re_path(r'^/slot/export/(?P<pk>[\d]+)$',
        SlotParticipantExportView.as_view(),
        name='slot-participant-export'),

    re_path(
        r'^/skills$',
        SkillList.as_view(),
        name='skill-list'
    ),
    re_path(
        r'^/skills/(?P<pk>\d+)$',
        SkillDetail.as_view(),
        name='skill'
    ),

    re_path(
        r'^/period/(?P<pk>\d+)$',
        PeriodActivityDetailView.as_view(),
        name="period-detail",
    ),
    re_path(r"^/deadline", include("bluebottle.time_based.urls.deadline_api")),
    re_path(r"^/periodic", include("bluebottle.time_based.urls.periodic_api")),
    re_path(r"^/schedule", include("bluebottle.time_based.urls.schedule_api")),
    re_path(r"^/teams", include("bluebottle.time_based.urls.team_api")),
]
