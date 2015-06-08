from django.conf.urls import patterns, url, include
from surlex.dj import surl
from ..views import PartnerDetail, PartnerList

urlpatterns = patterns('',
    surl(r'^<slug:s>$', PartnerDetail.as_view(), name='partner-detail'),
    url(r'^$', PartnerList.as_view(), name='partner-list')
)
