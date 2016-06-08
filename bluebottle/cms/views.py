from rest_framework import generics

from bluebottle.cms.models import Page
from bluebottle.cms.serializers import PageSerializer


class PageList(generics.ListAPIView):
    queryset = Page.objects.all()
    serializer_class = PageSerializer


class PageDetail(generics.RetrieveAPIView):
    serializer_class = PageSerializer
