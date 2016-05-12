from rest_framework import generics

from .models import Category
from .serializers import CategorySerializer


class CategoryList(generics.ListAPIView):
    model = Category
    serializer_class = CategorySerializer
