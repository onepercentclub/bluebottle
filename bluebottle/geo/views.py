from rest_framework import generics
from bluebottle.geo.models import Location
from bluebottle.geo.serializers import LocationSerializer
from bluebottle.projects.models import Project
from bluebottle.utils.views import ExpiresMixin

from .serializers import CountrySerializer
from .models import Country


class CountryList(ExpiresMixin, generics.ListAPIView):
    serializer_class = CountrySerializer
    queryset = Country.objects.all()

    def get_queryset(self):
        return self.queryset.filter(alpha2_code__isnull=False).order_by(
            'name').all()


class CountryDetail(generics.RetrieveAPIView):
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


class LocationList(ExpiresMixin, generics.ListAPIView):
    serializer_class = LocationSerializer
    queryset = Location.objects.all()
