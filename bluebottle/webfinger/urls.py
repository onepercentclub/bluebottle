from django.urls import re_path

from bluebottle.webfinger.views import (
    WebFingerView
)

urlpatterns = [
    re_path(r'^$', WebFingerView.as_view(), name='webfinger'),
]
