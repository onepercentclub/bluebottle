from django.conf.urls import url

from ..views import CountryList, CountryDetail, LocationList, GeolocationList, OfficeList, OfficeDetail

urlpatterns = [
    url(r'^countries/$', CountryList.as_view(),
        name='country-list'),
    url(r'^countries/(?P<pk>\d+)$', CountryDetail.as_view(),
        name='country-detail'),

    # Remove this after we deployed json-api office locations
    url(r'^locations/$', LocationList.as_view(),
        name='location-list'),

    url(r'^offices/$', OfficeList.as_view(),
        name='office-list'),
    url(r'^offices/(?P<pk>\d+)$', OfficeDetail.as_view(),
        name='office-detail'),

    url(r'^geolocations$', GeolocationList.as_view(),
        name='geolocation-list'),
]
