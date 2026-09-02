from django.urls import path

from bluebottle.voting.views import PollDetail, PollVoteDetail, PollVoteList

urlpatterns = [
    path('votes', PollVoteList.as_view(), name='poll-vote-list'),
    path('votes/<int:pk>', PollVoteDetail.as_view(), name='poll-vote-detail'),
    path('<int:pk>', PollDetail.as_view(), name='poll-detail'),
]
