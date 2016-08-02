from rest_framework import generics
from rest_framework.permissions import DjangoModelPermissions

from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from .models import ProjectPayout
from .serializers import PayoutSerializer


class PayoutList(generics.ListAPIView):
    queryset = ProjectPayout.objects.all()
    serializer_class = PayoutSerializer
    pagination_class = BluebottlePagination
    permission_classes = [DjangoModelPermissions]
    filter_fields = ('status',)


class PayoutDetail(generics.RetrieveUpdateAPIView):
    queryset = ProjectPayout.objects.all()
    serializer_class = PayoutSerializer
    permission_classes = [DjangoModelPermissions]

