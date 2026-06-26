from django.urls import path
from django.urls import re_path

from bluebottle.geo.views import (
    CountryList, CountryDetail, LocationList, GeolocationList, GeolocationDetail,
    OfficeList, OfficeDetail, PlaceList, PlaceDetail, NewCountryList
)

urlpatterns = [
    path(
        'countries/',
        CountryList.as_view(),
        name='country-list'
    ),
    path(
        'countries/<int:pk>',
        CountryDetail.as_view(),
        name='country-detail'
    ),

    # Remove this after we deployed json-api office locations
    path(
        'locations/',
        LocationList.as_view(),
        name='location-list'
    ),

    path(
        'offices/',
        OfficeList.as_view(),
        name='office-list'
    ),
    path(
        'offices/<int:pk>',
        OfficeDetail.as_view(),
        name='office-detail'
    ),

    path(
        'geolocations',
        GeolocationList.as_view(),
        name='geolocation-list'
    ),
    path(
        'geolocations/<int:pk>',
        GeolocationDetail.as_view(),
        name='geolocation-detail'
    ),

    re_path(
        r'^places(/)?$',
        PlaceList.as_view(),
        name='place-list'
    ),

    path(
        'places/<int:pk>',
        PlaceDetail.as_view(),
        name='place-detail'
    ),

    path(
        'countries-list/',
        NewCountryList.as_view(),
        name='new-country-list'
    ),
]
