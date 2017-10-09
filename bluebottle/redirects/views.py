from rest_framework import generics

from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from .models import Redirect
from .serializers import RedirectSerializer


class RedirectPagination(BluebottlePagination):
    page_size = 200


class RedirectListView(generics.ListAPIView):
    queryset = Redirect.objects.all()
    serializer_class = RedirectSerializer
    pagination_class = RedirectPagination
