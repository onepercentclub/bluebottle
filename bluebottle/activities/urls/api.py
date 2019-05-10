from django.conf.urls import url

from bluebottle.activities.views import ActivityList

urlpatterns = [
    url(r'^$', ActivityList.as_view(), name='activities-list'),
]
