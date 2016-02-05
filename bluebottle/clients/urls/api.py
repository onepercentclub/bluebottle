from django.conf.urls import url

from bluebottle.clients.views import SettingsView

urlpatterns = [
    url(r'^$', SettingsView.as_view(), name='settings')
]
