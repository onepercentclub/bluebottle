from django.conf.urls import patterns, url

from ..views import RedirectListView

urlpatterns = patterns('', url(r'^/$', RedirectListView.as_view(), name='redirect-list'),)
