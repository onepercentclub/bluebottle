from rest_framework import generics
from .models import Quote
from .serializers import QuoteSerializer
from django.utils.timezone import now
from django.db.models import Q


# API views

class QuoteList(generics.ListAPIView):
    model = Quote
    serializer_class = QuoteSerializer
    paginate_by = 10

    def get_queryset(self):
        qs = super(QuoteList, self).get_queryset()

        # Set language if supplied
        language = self.request.QUERY_PARAMS.get('language', None)
        if language:
            qs = qs.filter(language=language)

        qs = qs.filter(status=Quote.QuoteStatus.published)
        qs = qs.filter(publication_date__lte=now)
        qs = qs.filter(Q(publication_end_date__gte=now) | Q(publication_end_date__isnull=True))
        return qs

