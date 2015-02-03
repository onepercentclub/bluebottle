from rest_framework import generics
from bluebottle.suggestions.models import Suggestion
from bluebottle.utils.serializers import DefaultSerializerMixin

class SuggestionList(DefaultSerializerMixin, generics.ListAPIView):
    model = Suggestion

    # def get_queryset(self):
    #     qs = super(ProjectList, self).get_queryset()
    #     status = self.request.QUERY_PARAMS.get('status', None)
    #     if status:
    #         qs = qs.filter(Q(status_id=status))
    #     return qs.filter(status__viewable=True)


class SuggestionDetail(DefaultSerializerMixin, generics.RetrieveAPIView):
    model = Suggestion

    # def get_queryset(self):
    #     qs = super(ProjectDetail, self).get_queryset()
    #     return qs