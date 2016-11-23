from django.conf.urls import url

from bluebottle.cms.views import PageList, Page

urlpatterns = [
    url(r'^pages$', PageList.as_view(), name='page_list'),
    url(r'^pages/(?P<pk>[\d]+)$', Page.as_view(), name='page_detail'),
]
