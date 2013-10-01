from rest_framework import generics

from .serializers import CountrySerializer
from .models import Country


class CountryList(generics.ListAPIView):
    model = Country
    serializer_class = CountrySerializer

    def get_queryset(self):
        return Country.objects.filter(alpha2_code__isnull=False).order_by('name').all()

