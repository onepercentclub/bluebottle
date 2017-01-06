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
    filter_fields = ('language',)

    def get_queryset(self, *args, **kwargs):
        qs = super(NewsItemPreviewList, self).get_queryset()
        qs = qs.published()
        qs = qs.order_by('-publication_date')
        return qs


class NewsItemList(generics.ListAPIView):
    queryset = NewsItem.objects.all()
    serializer_class = NewsItemSerializer
    pagination_class = NewsItemPagination
    filter_fields = ('language',)

    def get_queryset(self, *args, **kwargs):
        qs = super(NewsItemList, self).get_queryset()
        qs = qs.published()
        qs = qs.order_by('-publication_date')
        return qs


class NewsItemDetail(generics.RetrieveAPIView):
    queryset = NewsItem.objects.all()
    serializer_class = NewsItemSerializer
    lookup_field = 'slug'

    def get_queryset(self, *args, **kwargs):
        qs = super(NewsItemDetail, self).get_queryset()
        qs = qs.published()
        return qs
