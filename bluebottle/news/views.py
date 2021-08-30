from bluebottle.utils.utils import get_language_from_request
from django.http import Http404
from rest_framework import generics

from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from .models import NewsItem
from .serializers import NewsItemSerializer, NewsItemPreviewSerializer


class NewsItemPagination(BluebottlePagination):
    page_size = 5


class NewsItemPreviewList(generics.ListAPIView):
    queryset = NewsItem.objects.all()
    serializer_class = NewsItemPreviewSerializer
    pagination_class = NewsItemPagination
    filterset_fields = ('language',)

    def get_queryset(self, *args, **kwargs):
        qs = super(NewsItemPreviewList, self).get_queryset()
        qs = qs.published()
        qs = qs.order_by('-publication_date')
        return qs


class NewsItemList(generics.ListAPIView):
    queryset = NewsItem.objects.all()
    serializer_class = NewsItemSerializer
    pagination_class = NewsItemPagination
    filterset_fields = ('language',)

    def get_queryset(self, *args, **kwargs):
        qs = super(NewsItemList, self).get_queryset()
        qs = qs.published()
        qs = qs.order_by('-publication_date')
        return qs


class NewsItemDetail(generics.RetrieveAPIView):
    queryset = NewsItem.objects.all()
    serializer_class = NewsItemSerializer

    def get_object(self):
        language = get_language_from_request(self.request)
        queryset = self.queryset.published()
        queryset = queryset.filter(slug=self.kwargs['slug'])
        if queryset.count() > 1:
            obj = queryset.filter(language=language).first()
        else:
            try:
                obj = queryset.get()
            except NewsItem.DoesNotExist:
                raise Http404('No news item with that slug.')

        self.check_object_permissions(self.request, obj)

        return obj
