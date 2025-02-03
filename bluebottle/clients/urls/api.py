from django.conf.urls import url

from bluebottle.clients.views import SettingsView, Robots

urlpatterns = [
    url(r'^$', SettingsView.as_view(), name='settings'),
    url(r'^/robots$', Robots.as_view(), name='robots')
]
