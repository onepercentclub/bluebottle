from django.conf.urls import url

from bluebottle.activities.views import ActivityList, ActivityDetail

urlpatterns = [
    url(r'^$', ActivityList.as_view(), name='activity-list'),
    url(r'^/(?P<pk>\d+)$', ActivityDetail.as_view(), name='activity-detail'),
]
