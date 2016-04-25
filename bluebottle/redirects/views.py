from rest_framework import generics

from .models import Redirect
from .serializers import RedirectSerializer


class RedirectListView(generics.ListAPIView):
    paginate_by = 100
    model = Redirect
    serializer_class = RedirectSerializer
