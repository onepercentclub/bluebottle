from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView
from rest_framework_json_api.views import AutoPrefetchMixin

from bluebottle.geo.models import Location, Country, Geolocation
from bluebottle.geo.serializers import LocationSerializer, GeolocationSerializer
from bluebottle.projects.models import Project
from bluebottle.utils.views import TranslatedApiViewMixin, JsonApiViewMixin
from .serializers import CountrySerializer


class CountryList(TranslatedApiViewMixin, ListAPIView):
    serializer_class = CountrySerializer
    queryset = Country.objects

    def get_queryset(self):
        qs = super(CountryList, self).get_queryset()
        return qs.filter(alpha2_code__isnull=False).all()


class CountryDetail(RetrieveAPIView):
    serializer_class = CountrySerializer
    queryset = Country.objects.all()

    def get_queryset(self):
        qs = super(CountryDetail, self).get_queryset()
        return qs


class UsedCountryList(CountryList):
    def get_queryset(self):
        qs = super(UsedCountryList, self).get_queryset()
        project_country_ids = Project.objects.filter(
            status__viewable=True).values_list('country', flat=True).distinct()

        return qs.filter(id__in=project_country_ids)


class LocationList(ListAPIView):
    serializer_class = LocationSerializer
    queryset = Location.objects.all()


class GeolocationList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    queryset = Geolocation.objects.all()
    serializer_class = GeolocationSerializer

    prefetch_for_includes = {
        'country': ['country'],
    }
