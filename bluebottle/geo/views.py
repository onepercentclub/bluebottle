from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView
from rest_framework_json_api.parsers import JSONParser
from rest_framework_json_api.views import AutoPrefetchMixin
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from bluebottle.bluebottle_drf2.renderers import BluebottleJSONAPIRenderer
from bluebottle.geo.models import Location, Country, InitiativePlace
from bluebottle.geo.serializers import LocationSerializer, InitiativePlaceSerializer
from bluebottle.projects.models import Project
from bluebottle.utils.views import TranslatedApiViewMixin
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


class InitiativePlaceList(AutoPrefetchMixin, CreateAPIView):
    queryset = InitiativePlace.objects.all()
    serializer_class = InitiativePlaceSerializer

    authentication_classes = (
        JSONWebTokenAuthentication,
    )

    parser_classes = (JSONParser,)

    renderer_classes = (BluebottleJSONAPIRenderer,)

    prefetch_for_includes = {
        'country': ['country'],
    }
