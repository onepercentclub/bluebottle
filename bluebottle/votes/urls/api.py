from django.conf.urls import url

from ..views import VoteList

urlpatterns = [
    url(r'^$', VoteList.as_view(), name='vote_list'),
]
