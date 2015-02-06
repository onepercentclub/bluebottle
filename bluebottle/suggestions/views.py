from rest_framework import generics
from bluebottle.suggestions.models import Suggestion
from bluebottle.suggestions.serializers import SuggestionSerializer

class SuggestionList(generics.ListCreateAPIView):
    model = Suggestion

    serializer_class = SuggestionSerializer


    def get_queryset(self):
        qs = Suggestion.objects.all()
        
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
 
    def pre_save(self, obj):
        import pdb;pdb.set_trace()


class SuggestionDetail(generics.RetrieveUpdateAPIView):
    model = Suggestion

    serializer_class = SuggestionSerializer
