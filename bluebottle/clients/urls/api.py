from django.urls import re_path

from bluebottle.clients.views import SettingsView

urlpatterns = [
    re_path(r'^$', SettingsView.as_view(), name='settings')
]
