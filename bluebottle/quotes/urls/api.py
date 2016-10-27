from django.conf.urls import url

from ..views import QuoteList


urlpatterns = [
    url(r'^$', QuoteList.as_view(), name='quote_list'),
]
