from rest_framework import generics

from bluebottle.cms.models import Page
from bluebottle.cms.serializers import PageSerializer


class PageList(generics.ListCreateAPIView):
    queryset = Page.objects.all()
    serializer_class = PageSerializer


class Page(generics.RetrieveAPIView):
    queryset = Page.objects.all()
    serializer_class = PageSerializer
