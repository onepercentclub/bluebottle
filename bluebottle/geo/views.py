from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView
from rest_framework_json_api.views import AutoPrefetchMixin

from bluebottle.geo.models import Location, Country, Geolocation
from bluebottle.geo.serializers import LocationSerializer, GeolocationSerializer
from bluebottle.utils.views import TranslatedApiViewMixin, JsonApiViewMixin
from .serializers import CountrySerializer


class CountryList(TranslatedApiViewMixin, ListAPIView):
    serializer_class = CountrySerializer
    queryset = Country.objects

    public_statuses = [
        'open', 'running', 'full', 'succeeded', 'partially_funded', 'refunded',
    ]

    @method_decorator(cache_page(3600))
    def get(self, request, *args, **kwargs):
        return super(CountryList, self).get(request, *args, **kwargs)

    def get_queryset(self):
        qs = super(CountryList, self).get_queryset().filter(
            alpha2_code__isnull=False
        )

        if 'filter[used]' in self.request.GET:
            return qs.filter(
                Q(geolocation__initiative__status='approved') |
                Q(geolocation__event__status__in=self.public_statuses) |
                Q(geolocation__assignment__status__in=self.public_statuses)
            ).distinct()
        else:
            return qs


class CountryDetail(RetrieveAPIView):
    serializer_class = CountrySerializer
    queryset = Country.objects.all()

    def get_queryset(self):
        qs = super(CountryDetail, self).get_queryset()
        return qs


class LocationList(ListAPIView):
    serializer_class = LocationSerializer
    queryset = Location.objects.all()


class GeolocationList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    queryset = Geolocation.objects.all()
    serializer_class = GeolocationSerializer

    prefetch_for_includes = {
        'country': ['country'],
    }
