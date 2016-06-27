from rest_framework import generics

from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from .models import Quote
from .serializers import QuoteSerializer
from django.utils.timezone import now
from django.db.models import Q


# API views
class QuoteList(generics.ListAPIView):
    queryset = Quote.objects.all()
    serializer_class = QuoteSerializer
    pagination_class = BluebottlePagination
    filter_fields = ('language',)

    def get_queryset(self):
        qs = super(QuoteList, self).get_queryset()
        qs = qs.filter(status=Quote.QuoteStatus.published)
        qs = qs.filter(publication_date__lte=now())
        qs = qs.filter(Q(publication_end_date__gte=now()) | Q(
            publication_end_date__isnull=True))
        return qs
