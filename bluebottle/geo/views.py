from rest_framework import generics

from bluebottle.projects import get_project_model

from .serializers import CountrySerializer
from .models import Country

PROJECT_MODEL = get_project_model()

class CountryList(generics.ListAPIView):
    model = Country
    serializer_class = CountrySerializer

    def get_queryset(self):
        return Country.objects.filter(alpha2_code__isnull=False).order_by('name').all()

class UsedCountryList(CountryList):

    def get_queryset(self):
        qs = super(UsedCountryList, self).get_queryset()

        project_country_ids = PROJECT_MODEL.objects.values_list('country', flat=True).distinct()

        return qs.filter(id__in=project_country_ids)
