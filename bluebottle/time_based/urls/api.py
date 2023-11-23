from django.conf.urls import url

from bluebottle.time_based.views import (
    DateActivityListView, PeriodActivityListView,
    DateActivityDetailView, PeriodActivityDetailView,
    DateActivityRelatedParticipantList, PeriodActivityRelatedParticipantList,
    DateTransitionList, PeriodTransitionList,
    DateParticipantList, DateParticipantDetail,
    DateParticipantTransitionList, DateParticipantDocumentDetail,
    PeriodParticipantList, PeriodParticipantDetail,
    PeriodParticipantTransitionList, PeriodParticipantDocumentDetail,
    TimeContributionDetail,
    DateSlotDetailView, DateSlotListView,
    SlotParticipantListView, SlotParticipantDetailView, SlotParticipantTransitionList,
    DateActivityIcalView, ActivitySlotIcalView, TeamSlotIcalView,
    DateParticipantExportView, PeriodParticipantExportView,
    SlotRelatedParticipantList, SkillList, SkillDetail,
    RelatedSlotParticipantListView, TeamSlotListView, TeamSlotDetailView, DateSlotTransitionList,
    SlotParticipantExportView
)

urlpatterns = [
    url(r'^/date$',
        DateActivityListView.as_view(),
        name='date-list'),

    url(r'^/period$',
        PeriodActivityListView.as_view(),
        name='period-list'),

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

    url(r'^/team/ical/(?P<pk>\d+)$',
        TeamSlotIcalView.as_view(),
        name='team-ical'),

    url(r'^/period/(?P<pk>\d+)$',
        PeriodActivityDetailView.as_view(),
        name='period-detail'),

    url(r'^/period/(?P<activity_id>\d+)/participants$',
        PeriodActivityRelatedParticipantList.as_view(),
        name='period-participants'),

    url(r'^/team/slots$',
        TeamSlotListView.as_view(),
        name='team-slot-list'),

    url(r'^/team/slots/(?P<pk>\d+)$',
        TeamSlotDetailView.as_view(),
        name='team-slot-detail'),

    url(r'^/date/transitions$',
        DateTransitionList.as_view(),
        name='date-transition-list'),


    url(r'^/slot/transitions$',
        DateSlotTransitionList.as_view(),
        name='slot-transition-list'),

    url(r'^/period/transitions$',
        PeriodTransitionList.as_view(),
        name='period-transition-list'),

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

    url(r'^/participants/period$',
        PeriodParticipantList.as_view(),
        name='period-participant-list'),
    url(r'^/participants/period/(?P<pk>\d+)$',
        PeriodParticipantDetail.as_view(),
        name='period-participant-detail'),
    url(r'^/participants/period/transitions$',
        PeriodParticipantTransitionList.as_view(),
        name='period-participant-transition-list'),
    url(r'^/participants/period/(?P<pk>\d+)/document$',
        PeriodParticipantDocumentDetail.as_view(),
        name='period-participant-document'),

    url(r'^/contributions/time/(?P<pk>\d+)$',
        TimeContributionDetail.as_view(),
        name='time-contribution-detail'),

    url(r'^/date/export/(?P<pk>[\d]+)$',
        DateParticipantExportView.as_view(),
        name='date-participant-export'),

    url(r'^/period/export/(?P<pk>[\d]+)$',
        PeriodParticipantExportView.as_view(),
        name='period-participant-export'),

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

]
