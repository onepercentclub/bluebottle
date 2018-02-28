from rest_framework import generics

from bluebottle.utils.views import ExpiresMixin

from .models import Category
from .serializers import CategorySerializer


class CategoryList(ExpiresMixin, generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CategoryDetail(generics.RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    lookup_field = 'slug'
