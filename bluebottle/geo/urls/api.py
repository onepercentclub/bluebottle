from django.conf.urls import patterns, url
from ..views import CountryList, UsedCountryList, CountryDetail


urlpatterns = patterns('',
    url(r'^countries/$', CountryList.as_view(), name='country-list'),
    url(r'^used_countries/$', UsedCountryList.as_view(), name='used-country-list'),

)