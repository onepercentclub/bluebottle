from django.conf.urls import url

from ..views import PageDetail, PageList

urlpatterns = [
    url(r'^(?P<language>[\w]+)/pages/$', PageList.as_view(), name='page_list'),
    url(r'^(?P<language>[\w]+)/pages/(?P<slug>[\-\w]+)$', PageDetail.as_view(),
        name='page_detail'),
]
