from rest_framework import generics
from rest_framework.pagination import PageNumberPagination

from .models import Redirect
from .serializers import RedirectSerializer


class RedirectPagination(PageNumberPagination):
    page_size = 100


class RedirectListView(generics.ListAPIView):
    queryset = Redirect.objects.all()
    serializer_class = RedirectSerializer
    pagination_class = RedirectPagination
