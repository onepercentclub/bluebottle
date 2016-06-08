from rest_framework import generics

from bluebottle.cms.models import Page
from bluebottle.cms.serializers import PageSerializer


class PageList(generics.ListAPIView):
    serializer_class = PageSerializer

    def get_queryset(self):
        return Page.objects.filter(live=True).all()


class PageDetail(generics.RetrieveAPIView):
    serializer_class = PageSerializer

    # FIXME privileged users should be able to retrieve
    # pages in draft too
    def get_queryset(self):
        return Page.objects.filter(live=True).all()
