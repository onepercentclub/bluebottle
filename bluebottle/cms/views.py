from rest_framework import generics

from bluebottle.cms.models import ResultPage
from bluebottle.cms.serializers import ResultPageSerializer


class ResultPageDetail(generics.RetrieveAPIView):
    queryset = ResultPage.objects.all()
    serializer_class = ResultPageSerializer

    def get_serializer_context(self):
        context = super(ResultPageDetail, self).get_serializer_context()
        obj = self.get_object()
        context['ha'] = 'oliebol'
        context['start_date'] = obj.start_date
        context['end_date'] = obj.end_date
        return context
