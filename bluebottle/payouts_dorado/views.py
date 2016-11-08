from rest_framework import generics
from rest_framework.permissions import IsAdminUser

from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from bluebottle.projects.models import Project
from bluebottle.projects.serializers import (
    ProjectPayoutSerializer
)


class ProjectPayoutList(generics.ListAPIView):
    pagination_class = BluebottlePagination
    queryset = Project.objects.filter(status__slug__in=['done-complete', 'done-incomplete']).order_by('-created').all()
    serializer_class = ProjectPayoutSerializer
    permission_classes = (IsAdminUser,)


class ProjectPayoutDetail(generics.RetrieveUpdateAPIView):
    queryset = Project.objects.filter(campaign_ended__isnull=False).all()
    serializer_class = ProjectPayoutSerializer
    permission_classes = (IsAdminUser,)
