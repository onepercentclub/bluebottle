from rest_framework import generics

from bluebottle.cms.models import ResultPage
from bluebottle.cms.serializers import ResultPageSerializer


class ResultPageDetail(generics.RetrieveAPIView):
    queryset = ResultPage.objects.all()
    serializer_class = ResultPageSerializer
