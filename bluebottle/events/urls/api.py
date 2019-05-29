from django.conf.urls import url

from bluebottle.events.views import (
    EventList, EventDetail,
    EventTransitionList,
    ParticipantList, ParticipantDetail,
    ParticipantTransitionList
)

urlpatterns = [
    url(r'^$', EventList.as_view(), name='event-list'),
    url(r'^/(?P<pk>[\d-]+)$', EventDetail.as_view(), name='event-detail'),
    url(
        r'^/transitions$',
        EventTransitionList.as_view(),
        name='event-transition-list'
    ),

    url(r'/participants$', ParticipantList.as_view(), name='participant-list'),
    url(r'^/participants/(?P<pk>[\d]+)$', ParticipantDetail.as_view(), name='participant-detail'),
    url(
        r'^/participants/transitions$',
        ParticipantTransitionList.as_view(),
        name='participant-transition-list'
    ),
]
