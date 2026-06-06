from django.urls import path

from bluebottle.webfinger.views import (
    WebFingerView
)

urlpatterns = [
    path('', WebFingerView.as_view(), name='webfinger'),
]
