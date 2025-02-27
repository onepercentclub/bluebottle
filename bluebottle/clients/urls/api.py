from django.urls import re_path

from bluebottle.clients.views import SettingsView, Robots

urlpatterns = [
    re_path(r'^$', SettingsView.as_view(), name='settings'),
    re_path(r'^/robots$', Robots.as_view(), name='robots')
]
