from django.conf.urls import url

from bluebottle.initiatives.views import InitiativeList, InitiativeDetail

urlpatterns = [
    url(r'^$', InitiativeList.as_view(), name='initiative-list'),
    url(r'^(?P<pk>\d+)$', InitiativeDetail.as_view(), name='initiative-detail'),
]
