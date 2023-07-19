from django.conf.urls import url

from bluebottle.updates.views import UpdateList, UpdateDetail, ActivityUpdateList

urlpatterns = [
    url(r'^$', UpdateList.as_view(), name='update-list'),
    url(r'^activity/(?P<activity_pk>\d+)$', ActivityUpdateList.as_view(), name='activity-update-list'),
    url(r'^(?P<pk>\d+)$', UpdateDetail.as_view(), name='update-detail'),
]
