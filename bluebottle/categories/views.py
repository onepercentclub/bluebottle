from django.utils.translation import get_language

from bluebottle.utils.views import (
    ListAPIView, RetrieveAPIView
)
from .models import Category
from .serializers import CategorySerializer


class CategoryList(ListAPIView):
    queryset = Category.objects.all()

    def get_queryset(self, *args, **kwargs):
        return self.queryset.translated(
            get_language()
        ).order_by('translations__title')

    serializer_class = CategorySerializer


class CategoryDetail(RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    lookup_field = 'slug'
