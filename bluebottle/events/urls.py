from django.conf.urls import url

from bluebottle.events.views import EventListView

urlpatterns = [
    url(r'^$', EventListView.as_view(), name='event-list'),
]
