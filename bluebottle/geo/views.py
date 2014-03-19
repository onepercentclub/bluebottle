from rest_framework import generics

from bluebottle.utils.utils import get_project_model

from .serializers import CountrySerializer
from .models import Country

PROJECT_MODEL = get_project_model()

class CountryList(generics.ListAPIView):
    model = Country
    serializer_class = CountrySerializer

    def get_queryset(self):
        queryset = Country.objects.filter(alpha2_code__isnull=False).order_by('name').all()
        name = self.request.QUERY_PARAMS.get('name', None)
        print name
        if name is not None:
            queryset = Country.objects.filter(name__iexact=name)
        return queryset
    #     qs = super(CountryList, self).get_queryset()
    #
    #     # Set language if supplied
    #     language = self.kwargs.get('language', None)
    #     if language:
    #         qs = qs.filter(language=language)
    #
    #     qs = qs.filter(status=Page.PageStatus.published)
    #     qs = qs.filter(publication_date__lte=now)
    #     qs = qs.filter(Q(publication_end_date__gte=now) |
    #                    Q(publication_end_date__isnull=True))
    #     return qs

        # return Country.objects.filter(alpha2_code__isnull=False).order_by('name').all()

class UsedCountryList(CountryList):

    def get_queryset(self):
        qs = super(UsedCountryList, self).get_queryset()

        project_country_ids = PROJECT_MODEL.objects.values_list('country', flat=True).distinct()

        return qs.filter(id__in=project_country_ids)
