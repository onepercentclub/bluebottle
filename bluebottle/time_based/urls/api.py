from django.conf.urls import include, url

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
    url(r'^/date$',
        DateActivityListView.as_view(),
        name='date-list'),

    url(r'^/date/(?P<pk>\d+)$',
        DateActivityDetailView.as_view(),
        name='date-detail'),

    url(r'^/date/(?P<activity_id>\d+)/participants$',
        DateActivityRelatedParticipantList.as_view(),
        name='date-participants'),

    url(r'^/date/slots/(?P<slot_id>\d+)/participants$',
        SlotRelatedParticipantList.as_view(),
        name='slot-participants'),

    url(r'^/date/slots$',
        DateSlotListView.as_view(),
        name='date-slot-list'),

    url(r'^/date/(?P<pk>\d+)/(?P<related_field>\w+)$',
        DateSlotListView.as_view(),
        name='date-slots'),

    url(r'^/date/slots/(?P<pk>\d+)$',
        DateSlotDetailView.as_view(),
        name='date-slot-detail'),

    url(r'^/date/ical/(?P<pk>\d+)/(?P<user_id>\d+)$',
        DateActivityIcalView.as_view(),
        name='date-ical'),

    url(r'^/slot/ical/(?P<pk>\d+)$',
        ActivitySlotIcalView.as_view(),
        name='slot-ical'),

    url(r'^/date/transitions$',
        DateTransitionList.as_view(),
        name='date-transition-list'),

    url(r'^/slot/transitions$',
        DateSlotTransitionList.as_view(),
        name='slot-transition-list'),

    url(r'^/participants/date$',
        DateParticipantList.as_view(),
        name='date-participant-list'),
    url(r'^/participants/date/(?P<pk>\d+)$',
        DateParticipantDetail.as_view(),
        name='date-participant-detail'),
    url(r'^/participants/date/transitions$',
        DateParticipantTransitionList.as_view(),
        name='date-participant-transition-list'),

    url(r'^/participants/date/(?P<pk>\d+)/document$',
        DateParticipantDocumentDetail.as_view(),
        name='date-participant-document'),

    url(r'^/slot-participants$',
        SlotParticipantListView.as_view(),
        name='slot-participant-list'),

    url(r'^/participants/date/(?P<participant_id>\d+)/slot-participants$',
        RelatedSlotParticipantListView.as_view(),
        name='related-slot-participant-list'),

    url(r'^/slot-participants/(?P<pk>\d+)$',
        SlotParticipantDetailView.as_view(),
        name='slot-participant-detail'),
    url(r'^/slot-participants/transitions$',
        SlotParticipantTransitionList.as_view(),
        name='slot-participant-transition-list'),

    url(r'^/contributions/time/(?P<pk>\d+)$',
        TimeContributionDetail.as_view(),
        name='time-contribution-detail'),

    url(r'^/date/export/(?P<pk>[\d]+)$',
        DateParticipantExportView.as_view(),
        name='date-participant-export'),

    url(r'^/slot/export/(?P<pk>[\d]+)$',
        SlotParticipantExportView.as_view(),
        name='slot-participant-export'),

    url(
        r'^/skills$',
        SkillList.as_view(),
        name='skill-list'
    ),
    url(
        r'^/skills/(?P<pk>\d+)$',
        SkillDetail.as_view(),
        name='skill'
    ),

    url(
        r'^/period/(?P<pk>\d+)$',
        PeriodActivityDetailView.as_view(),
        name="period-detail",
    ),
    url(r"^/deadline", include("bluebottle.time_based.urls.deadline_api")),
    url(r"^/periodic", include("bluebottle.time_based.urls.periodic_api")),
    url(r"^/schedule", include("bluebottle.time_based.urls.schedule_api")),
    url(r"^/teams", include("bluebottle.time_based.urls.team_api")),
]
