from rest_framework.generics import ListAPIView, RetrieveAPIView
from bluebottle.geo.models import Location
from bluebottle.geo.serializers import LocationSerializer
from bluebottle.projects.models import Project
from bluebottle.utils.views import TranslatedApiViewMixin

from .serializers import CountrySerializer
from .models import Country


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
