from django.utils.translation import get_language

from bluebottle.utils.views import (
    ListAPIView, RetrieveAPIView, JsonApiViewMixin, JsonApiPagination
)
from .models import Category
from .serializers import CategorySerializer


class CategoryPagination(JsonApiPagination):
    page_size = 50


class CategoryList(JsonApiViewMixin, ListAPIView):
    queryset = Category.objects.all()
    pagination_class = CategoryPagination

    def get_queryset(self, *args, **kwargs):
        return self.queryset.translated(
            get_language()
        ).order_by('translations__title')

    serializer_class = CategorySerializer


class CategoryDetail(JsonApiViewMixin, RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    lookup_field = 'slug'
