from django.conf.urls import patterns, url

from ..views import ShareFlyerView

urlpatterns = patterns(
    '',
    url(r'^share_flyer$', ShareFlyerView.as_view(), name='share_flyer'),
)
