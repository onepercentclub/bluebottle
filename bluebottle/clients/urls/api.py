from django.urls import path

from bluebottle.clients.views import SettingsView, Robots

urlpatterns = [
    path('', SettingsView.as_view(), name='settings'),
    path('/robots', Robots.as_view(), name='robots')
]
