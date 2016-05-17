from rest_framework import generics
from .models import NewsItem
from .serializers import NewsItemSerializer, NewsItemPreviewSerializer


class NewsItemPreviewList(generics.ListAPIView):
    queryset = NewsItem.objects.all()
    serializer_class = NewsItemPreviewSerializer
    paginate_by = 5
    filter_fields = ('language',)

    def get_queryset(self, *args, **kwargs):
        qs = super(NewsItemPreviewList, self).get_queryset()
        qs = qs.published()
        qs = qs.order_by('-publication_date')
        return qs


class NewsItemList(generics.ListAPIView):
    queryset = NewsItem.objects.all()
    serializer_class = NewsItemSerializer
    paginate_by = 5
    filter_fields = ('language',)

    def get_queryset(self, *args, **kwargs):
        qs = super(NewsItemList, self).get_queryset()
        qs = qs.published()
        qs = qs.order_by('-publication_date')
        return qs


class NewsItemDetail(generics.RetrieveAPIView):
    queryset = NewsItem.objects.all()
    serializer_class = NewsItemSerializer

    def get_queryset(self, *args, **kwargs):
        qs = super(NewsItemDetail, self).get_queryset()
        qs = qs.published()
        return qs
