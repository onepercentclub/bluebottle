from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.generics import (
    ListAPIView, RetrieveAPIView, CreateAPIView,
    RetrieveUpdateAPIView
)
from rest_framework.permissions import IsAuthenticated
from rest_framework_json_api.views import AutoPrefetchMixin

from bluebottle.geo.models import Location, Country, Geolocation, Place
from bluebottle.geo.serializers import (
    GeolocationSerializer, OfficeSerializer, OfficeListSerializer,
    InitiativeCountrySerializer, PlaceSerializer, CountrySerializer
)
from bluebottle.utils.views import TranslatedApiViewMixin, JsonApiViewMixin


class CountryList(TranslatedApiViewMixin, ListAPIView):
    serializer_class = CountrySerializer
    queryset = Country.objects

    public_statuses = [
        'open', 'running', 'full', 'succeeded', 'partially_funded', 'refunded',
    ]

    @method_decorator(cache_page(3600))
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = super(CountryList, self).get_queryset()

        if 'filter[used]' in self.request.GET:
            qs = qs.filter(
                Q(location__initiative__status='approved') |
                Q(geolocation__initiative__status='approved') |
                Q(geolocation__periodactivity__status__in=self.public_statuses) |
                (
                    Q(geolocation__dateactivityslot__activity__status__in=self.public_statuses) &
                    Q(geolocation__dateactivityslot__status__in=self.public_statuses)
                )
            )
        return qs


class CountryDetail(RetrieveAPIView):
    serializer_class = CountrySerializer
    queryset = Country.objects.all()

    def get_queryset(self):
        qs = super(CountryDetail, self).get_queryset()
        return qs


class OfficeList(JsonApiViewMixin, ListAPIView):
    serializer_class = OfficeListSerializer
    queryset = Location.objects.all()

    pagination_class = None
    permission_classes = [
        IsAuthenticated
    ]


class OfficeDetail(JsonApiViewMixin, RetrieveAPIView):
    serializer_class = OfficeSerializer
    queryset = Location.objects.all()


# Remove this after we deployed json-api office locations
class LocationList(ListAPIView):
    serializer_class = OfficeSerializer
    queryset = Location.objects.all()


class GeolocationList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    queryset = Geolocation.objects.all()
    serializer_class = GeolocationSerializer

    prefetch_for_includes = {
        'country': ['country'],
    }


class PlaceList(JsonApiViewMixin, CreateAPIView):
    queryset = Place.objects.all()

    serializer_class = PlaceSerializer
    permission_classes = [
        IsAuthenticated
    ]

    def perform_create(self, serializer):
        try:
            if 'mapbox_id' in serializer.validated_data:
                serializer.instance = Place.objects.get(
                    mapbox_id=serializer.validated_data['mapbox_id'],
                )
        except Place.DoesNotExist:
            pass

        return super().perform_create(serializer)


class PlaceDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    queryset = Place.objects.all()
    permission_classes = [
        IsAuthenticated
    ]
    serializer_class = PlaceSerializer


class NewCountryList(JsonApiViewMixin, ListAPIView):
    queryset = Country.objects.all()
    serializer_class = InitiativeCountrySerializer
    pagination_class = None
