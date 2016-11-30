from rest_framework import generics

from bluebottle.cms.serializers import PageSerializer


class PageList(generics.ListCreateAPIView):
    serializer_class = PageSerializer


class Page(generics.RetrieveAPIView):
    serializer_class = PageSerializer
