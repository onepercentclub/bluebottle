from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.timezone import now

from rest_framework import generics

from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from .models import Page
from .serializers import PageSerializer


class PageList(generics.ListAPIView):
    queryset = Page.objects.all()
    serializer_class = PageSerializer
    pagination_class = BluebottlePagination

    def get_queryset(self):
        qs = super(PageList, self).get_queryset()

        # Set language if supplied
        language = self.kwargs.get('language', None)
        if language:
            qs = qs.filter(language=language)

        qs = qs.filter(status=Page.PageStatus.published)
        qs = qs.filter(publication_date__lte=now())
        qs = qs.filter(Q(publication_end_date__gte=now()) |
                       Q(publication_end_date__isnull=True))
        return qs


class PageDetail(generics.RetrieveAPIView):
    queryset = Page.objects.all()
    serializer_class = PageSerializer

    def get_queryset(self):
        qs = super(PageDetail, self).get_queryset()
        qs = qs.filter(status=Page.PageStatus.published)
        qs = qs.filter(publication_date__lte=now())
        qs = qs.filter(Q(publication_end_date__gte=now()) |
                       Q(publication_end_date__isnull=True))
        return qs

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset,
                                language=self.kwargs['language'],
                                slug=self.kwargs['slug'])

        return obj
