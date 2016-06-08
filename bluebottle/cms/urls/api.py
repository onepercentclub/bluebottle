from django.conf.urls import patterns, url

from ..views import PageDetail, PageList

urlpatterns = patterns(
    '',

    url(r'^$',
        PageList.as_view(),
        name='cms_page_list'),

    url(r'^(?P<pk>\d+)$',
        PageDetail.as_view(),
        name='cms_page_detail'),
)
