from django.urls import path, re_path

from bluebottle.voting.views import (
    PollDetail, PollVoteDetail, PollVoteExportView, PollVoteList
)

urlpatterns = [
    path('votes', PollVoteList.as_view(), name='poll-vote-list'),
    path('votes/<int:pk>', PollVoteDetail.as_view(), name='poll-vote-detail'),
    re_path(
        r'^export/(?P<pk>[\d]+)$',
        PollVoteExportView.as_view(),
        name='poll-vote-export'
    ),
    path('<int:pk>', PollDetail.as_view(), name='poll-detail'),
]
