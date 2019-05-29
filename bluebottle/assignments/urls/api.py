from django.conf.urls import url

from bluebottle.events.views import (
    EventList, EventDetail, ParticipantList, ParticipantDetail
)

urlpatterns = [
    url(r'^$', EventList.as_view(), name='event-list'),
    url(r'^(?P<slug>[\w-]+)$', EventDetail.as_view(), name='event-detail'),

    url(r'participants/^$', ParticipantList.as_view(), name='participant-list'),
    url(r'^participants/(?P<id>[\d]+)$', ParticipantDetail.as_view(), name='participant-detail'),
]
