from django.urls import re_path

from bluebottle.geo.views import (
    CountryList, CountryDetail, LocationList, GeolocationList, OfficeList, OfficeDetail,
    PlaceList, PlaceDetail, NewCountryList
)

urlpatterns = [
    re_path(r'^countries/$', CountryList.as_view(),
        name='country-list'),
    re_path(r'^countries/(?P<pk>\d+)$', CountryDetail.as_view(),
        name='country-detail'),

    # Remove this after we deployed json-api office locations
    re_path(r'^locations/$', LocationList.as_view(),
        name='location-list'),

    re_path(r'^offices/$', OfficeList.as_view(),
        name='office-list'),
    re_path(r'^offices/(?P<pk>\d+)$', OfficeDetail.as_view(),
        name='office-detail'),

    re_path(r'^geolocations$', GeolocationList.as_view(),
        name='geolocation-list'),

    re_path(r'^places(/)?$', PlaceList.as_view(),
        name='place-list'),

    re_path(r'^places/(?P<pk>\d+)$', PlaceDetail.as_view(),
        name='place-detail'),

    re_path(r'^countries-list/$', NewCountryList.as_view(),
        name='new-country-list'),
]
