from bluebottle.utils.views import (
    ListAPIView, RetrieveAPIView
)
from .models import Category
from .serializers import CategorySerializer


class CategoryList(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CategoryDetail(RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    lookup_field = 'slug'
