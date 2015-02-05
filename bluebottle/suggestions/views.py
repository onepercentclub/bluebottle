from rest_framework import generics
from bluebottle.suggestions.models import Suggestion


class SuggestionList(generics.ListAPIView):
    model = Suggestion

    def get_queryset(self):
        qs = Suggestion.objects.all()
        
        destination = self.request.QUERY_PARAMS.get('destination', None)
        status = self.request.QUERY_PARAMS.get('status', None)

        if destination:
            qs = qs.filter(destination__iexact=destination)
        if status:
            qs = qs.filter(status__iexact=status)
        return qs.order_by('deadline')


class SuggestionDetail(generics.RetrieveAPIView):
    model = Suggestion