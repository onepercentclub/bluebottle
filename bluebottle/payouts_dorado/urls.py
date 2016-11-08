from django.conf.urls import url

from .views import ProjectPayoutDetail


urlpatterns = [
    url(r'^projects/(?P<pk>[\d]+)$',
        ProjectPayoutDetail.as_view(),
        name='project-payout-detail'),
]
