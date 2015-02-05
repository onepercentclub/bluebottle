from rest_framework import generics
from bluebottle.suggestions.models import Suggestion


class SuggestionList(generics.ListAPIView):
    model = Suggestion


class SuggestionDetail(generics.RetrieveAPIView):
    model = Suggestion