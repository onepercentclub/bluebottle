from django.conf.urls import url

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
    url(r'^$',
        DateActivityListView.as_view(),
        name='date-list'),
    url(r'^/(?P<pk>\d+)$',
        DateActivityDetailView.as_view(),
        name='date-detail'),
    url(r'^/transitions$',
        DateTransitionList.as_view(),
        name='date-transition-list'),

    url(r'^/(?P<activity_id>\d+)/registrations/$',
        DateRelatedRegistrationList.as_view(),
        name='related-date-registrations'),
    url(r'^/registrations/$',
        DateRegistrationList.as_view(),
        name='date-registration-list'),
    url(r'^/registrations/transitions$',
        DateRegistrationTransitionList.as_view(),
        name='date-registration-transitions'),
    url(r'^/registrations/(?P<pk>\d+)$',
        DateRegistrationDetail.as_view(),
        name='date-registration-detail'),
    url(r'^/registrations/(?P<pk>\d+)/document$',
        DateRegistrationDocumentDetail.as_view(),
        name='date-registration-document'),

    url(r'^/(?P<activity_id>\d+)/participants$',
        DateRelatedParticipantList.as_view(),
        name='date-related-participants'),

    url(r'^/participants$',
        DateParticipantList.as_view(),
        name='date-participant-create'),

    url(r'^/participants/transitions$',
        DateParticipantTransitionList.as_view(),
        name='date-participant-transitions'),
    url(r'^/participants/(?P<pk>\d+)$',
        DateParticipantDetail.as_view(),
        name='date-participant-detail'),

    url(r'^/slots$',
        DateSlotListView.as_view(),
        name='date-slot-list'),

    url(r'^/(?P<activity_id>\d+)/slots$',
        RelatedDateSlotListView.as_view(),
        name='related-date-slots'),

    url(r'^/slots/(?P<pk>\d+)$',
        DateSlotDetailView.as_view(),
        name='date-slot-detail'),

    url(r'^/slots/(?P<slot_id>\d+)/participants$',
        DateSlotRelatedParticipantView.as_view(),
        name='date-slot-related-participants'),

    url(r'^/export/(?P<pk>[\d]+)$',
        DateParticipantExportView.as_view(),
        name='date-participant-export'),

    url(r'^/ical/(?P<pk>\d+)/(?P<user_id>\d+)$',
        DateActivityIcalView.as_view(),
        name='date-ical'),

    url(r'^/slot/ical/(?P<pk>\d+)$',
        ActivitySlotIcalView.as_view(),
        name='slot-ical'),


]
