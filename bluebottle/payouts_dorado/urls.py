from django.conf.urls import url

from .views import ProjectPayoutDetail, PayoutMethodList


urlpatterns = [
    url(r'^projects/(?P<pk>[\d]+)$',
        ProjectPayoutDetail.as_view(),
        name='project-payout-detail'),
    url(r'^methods/$',
        PayoutMethodList.as_view(),
        name='payout-method-list'),
]
