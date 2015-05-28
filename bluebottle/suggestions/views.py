from datetime import date
from rest_framework import generics, status, response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action

from bluebottle.suggestions.models import Suggestion
from bluebottle.suggestions.serializers import SuggestionSerializer


class SuggestionList(generics.ListCreateAPIView):
    model = Suggestion
    permission_classes = (IsAuthenticated, )
    serializer_class = SuggestionSerializer

    def get_queryset(self):
        qs = Suggestion.objects.filter(deadline__gte=date.today())

        destination = self.request.QUERY_PARAMS.get('destination', None)
        status = self.request.QUERY_PARAMS.get('status', None)
        project_slug = self.request.QUERY_PARAMS.get('project_slug', None)

        if project_slug:
            qs = qs.filter(project__slug=project_slug)
        if destination:
            qs = qs.filter(destination__iexact=destination)
        if status:
            qs = qs.filter(status__iexact=status)
        return qs.order_by('deadline')


class SuggestionDetail(generics.RetrieveUpdateAPIView):
    model = Suggestion
    permission_classes = (IsAuthenticated, )
    serializer_class = SuggestionSerializer


class SuggestionToken(generics.RetrieveUpdateAPIView):
    model = Suggestion
    permission_classes = (IsAuthenticated, )
    serializer_class = SuggestionSerializer
    lookup_field = 'token'

    def update(self, request, *args, **kwargs):
        suggestion = self.get_object()

        if suggestion.confirm():
            return response.Response({'status':'validated'},
                                     status=status.HTTP_200_OK)
        return response.Response({'status':'not validated'},
                                 status=status.HTTP_400_BAD_REQUEST)
