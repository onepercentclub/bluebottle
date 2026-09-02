from django.urls import path

from bluebottle.voting.views import PollDetail

urlpatterns = [
    path('<int:pk>', PollDetail.as_view(), name='poll-detail'),
]
