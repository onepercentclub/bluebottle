from django.conf.urls import patterns, url
from bluebottle.bb_accounts.urls.api import urlpatterns
from ..views import UserSettingsDetail

urlpatterns += patterns('',
     url(r'^settings/(?P<pk>\d+)$', UserSettingsDetail.as_view(),
        name='user-settings-detail'),
)

