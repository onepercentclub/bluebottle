from django.conf.urls import patterns, url

from ..views import PageDetail, PageList, PageDraftDetail

urlpatterns = patterns(
    '',

    url(r'^$',
        PageList.as_view(),
        name='cms_page_list'),

    url(r'^(?P<pk>\d+)$',
        PageDetail.as_view(),
        name='cms_page_detail'),

    url(r'^preview/(?P<pk>\d+)$',
        PageDraftDetail.as_view(),
        name='cms_page_draft_detail'),
)
