from rest_framework import generics

from bluebottle.utils.views import ModelTranslationViewMixin
from .models import Category
from .serializers import CategorySerializer



class CategoryList(ModelTranslationViewMixin, generics.ListAPIView):
    model = Category
    serializer_class = CategorySerializer




