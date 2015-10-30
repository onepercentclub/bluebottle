from rest_framework import generics
from bluebottle.geo.models import Location
from bluebottle.geo.serializers import LocationSerializer

from bluebottle.utils.model_dispatcher import get_project_model

from .serializers import CountrySerializer

PROJECT_MODEL = get_project_model()


class CountryList(generics.ListAPIView):
    serializer_class = CountrySerializer
    model = serializer_class.Meta.model

    def get_queryset(self):
        return self.model.objects.filter(alpha2_code__isnull=False).order_by(
            'name').all()


class CountryDetail(generics.RetrieveAPIView):
    serializer_class = CountrySerializer
    model = serializer_class.Meta.model

    def get_queryset(self):
        qs = super(CountryDetail, self).get_queryset()
        return qs


class UsedCountryList(CountryList):
    def get_queryset(self):
        qs = super(UsedCountryList, self).get_queryset()
        project_country_ids = PROJECT_MODEL.objects.filter(
            status__viewable=True).values_list('country', flat=True).distinct()

        return qs.filter(id__in=project_country_ids)


class LocationList(generics.ListAPIView):
    serializer_class = LocationSerializer
    model = Location
