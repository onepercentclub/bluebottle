from rest_framework import generics

from .models import Redirect
from .serializers import RedirectSerializer


class RedirectListView(generics.ListAPIView):
    model = Redirect
    serializer_class = RedirectSerializer
