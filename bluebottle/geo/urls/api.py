from django.conf.urls import patterns, url
from ..views import CountryList, UsedCountryList, CountryDetail, LocationList


urlpatterns = patterns('',
    url(r'^countries/$', CountryList.as_view(), name='country-list'),
    url(r'^countries/(?P<pk>\d+)$', CountryDetail.as_view(), name='country-detail'),
    url(r'^used_countries/$', UsedCountryList.as_view(), name='used-country-list'),
    url(r'^locations/$', LocationList.as_view(), name='location-list'),
)