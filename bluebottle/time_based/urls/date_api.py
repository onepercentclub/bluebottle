from django.urls import re_path

from bluebottle.time_based.views import (
    DateTransitionList,
    DateActivityListView, DateActivityDetailView,
    DateRelatedRegistrationList, DateRegistrationList,
    DateRegistrationTransitionList,
    DateRegistrationDetail,
    DateRegistrationDocumentDetail, DateParticipantTransitionList, DateParticipantExportView,
    DateRelatedParticipantList, DateParticipantDetail, DateParticipantList,
    DateSlotRelatedParticipantView,
    DateActivityIcalView,
    DateSlotDetailView, DateSlotListView,
    ActivitySlotIcalView,
    RelatedDateSlotListView
)

urlpatterns = [
    re_path(
        r'^$',
        DateActivityListView.as_view(),
        name='date-list'
    ),
    re_path(
        r'^/(?P<pk>\d+)$',
        DateActivityDetailView.as_view(),
        name='date-detail'
    ),
    re_path(
        r'^/transitions$',
        DateTransitionList.as_view(),
        name='date-transition-list'
    ),

    re_path(
        r'^/(?P<activity_id>\d+)/registrations/$',
        DateRelatedRegistrationList.as_view(),
        name='related-date-registrations'
    ),
    re_path(
        r'^/registrations/$',
        DateRegistrationList.as_view(),
        name='date-registration-list'
    ),
    re_path(
        r'^/registrations/transitions$',
        DateRegistrationTransitionList.as_view(),
        name='date-registration-transitions'
    ),
    re_path(
        r'^/registrations/(?P<pk>\d+)$',
        DateRegistrationDetail.as_view(),
        name='date-registration-detail'
    ),
    re_path(
        r'^/registrations/(?P<pk>\d+)/document$',
        DateRegistrationDocumentDetail.as_view(),
        name='date-registration-document'
    ),

    re_path(
        r'^/(?P<activity_id>\d+)/participants$',
        DateRelatedParticipantList.as_view(),
        name='date-participants'
    ),

    re_path(
        r'^/participants$',
        DateParticipantList.as_view(),
        name='date-participant-list'
    ),

    re_path(
        r'^/participants/transitions$',
        DateParticipantTransitionList.as_view(),
        name='date-participant-transitions'
    ),
    re_path(
        r'^/participants/(?P<pk>\d+)$',
        DateParticipantDetail.as_view(),
        name='date-participant-detail'
    ),

    re_path(
        r'^/slots$',
        DateSlotListView.as_view(),
        name='date-slot-list'
    ),

    re_path(
        r'^/(?P<activity_id>\d+)/slots$',
        RelatedDateSlotListView.as_view(),
        name='related-date-slots'
    ),

    re_path(
        r'^/slots/(?P<pk>\d+)$',
        DateSlotDetailView.as_view(),
        name='date-slot-detail'
    ),

    re_path(
        r'^/slots/(?P<slot_id>\d+)/participants$',
        DateSlotRelatedParticipantView.as_view(),
        name='date-slot-related-participants'
    ),

    re_path(
        r'^/export/(?P<pk>[\d]+)$',
        DateParticipantExportView.as_view(),
        name='date-participant-export'
    ),

    re_path(
        r'^/ical/(?P<pk>\d+)/(?P<user_id>\d+)$',
        DateActivityIcalView.as_view(),
        name='date-ical'
    ),

    re_path(
        r'^/slot/ical/(?P<pk>\d+)$',
        ActivitySlotIcalView.as_view(),
        name='slot-ical'
    ),
]
