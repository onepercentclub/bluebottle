from django.urls import path
from django.urls import re_path

from bluebottle.time_based.views import (
    DateTransitionList,
    DateActivityListView, DateActivityDetailView,
    DateRegistrationList,
    DateRelatedRegistrationList,
    DateRegistrationTransitionList,
    DateRegistrationDetail,
    DateParticipantTransitionList, DateParticipantExportView,
    DateRelatedParticipantList, DateParticipantDetail, DateParticipantList,
    DateSlotRelatedParticipantView,
    DateActivityIcalView,
    DateSlotDetailView, DateSlotListView,
    ActivitySlotIcalView,
    RelatedDateSlotListView, DateRegistrationRelatedParticipantView
)

urlpatterns = [
    path(
        '',
        DateActivityListView.as_view(),
        name='date-list'
    ),
    path(
        '/<int:pk>',
        DateActivityDetailView.as_view(),
        name='date-detail'
    ),
    path(
        '/transitions',
        DateTransitionList.as_view(),
        name='date-transition-list'
    ),

    path(
        '/registrations/',
        DateRegistrationList.as_view(),
        name='date-registration-list'
    ),

    path(
        '/<int:activity_id>/registrations/',
        DateRelatedRegistrationList.as_view(),
        name='related-date-registrations'
    ),
    path(
        '/registrations/transitions',
        DateRegistrationTransitionList.as_view(),
        name='date-registration-transitions'
    ),
    path(
        '/registrations/<int:pk>',
        DateRegistrationDetail.as_view(),
        name='date-registration-detail'
    ),
    path(
        '/registrations/<int:registration_id>/participants',
        DateRegistrationRelatedParticipantView.as_view(),
        name='date-registration-related-participants'
    ),

    path(
        '/<int:activity_id>/participants',
        DateRelatedParticipantList.as_view(),
        name='date-participants'
    ),

    path(
        '/participants',
        DateParticipantList.as_view(),
        name='date-participant-list'
    ),

    path(
        '/participants/transitions',
        DateParticipantTransitionList.as_view(),
        name='date-participant-transitions'
    ),
    path(
        '/participants/<int:pk>',
        DateParticipantDetail.as_view(),
        name='date-participant-detail'
    ),

    path(
        '/slots',
        DateSlotListView.as_view(),
        name='date-slot-list'
    ),

    path(
        '/<int:activity_id>/slots',
        RelatedDateSlotListView.as_view(),
        name='related-date-slots'
    ),

    path(
        '/slots/<int:pk>',
        DateSlotDetailView.as_view(),
        name='date-slot-detail'
    ),

    path(
        '/slots/<int:slot_id>/participants',
        DateSlotRelatedParticipantView.as_view(),
        name='date-slot-related-participants'
    ),

    re_path(
        r'^/export/(?P<pk>[\d]+)$',
        DateParticipantExportView.as_view(),
        name='date-participant-export'
    ),

    path(
        '/ical/<int:pk>/<int:user_id>',
        DateActivityIcalView.as_view(),
        name='date-ical'
    ),

    path(
        '/slot/ical/<int:pk>',
        ActivitySlotIcalView.as_view(),
        name='slot-ical'
    ),
]
