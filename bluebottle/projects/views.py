from rest_framework import generics
from rest_framework.permissions import IsAdminUser

from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from bluebottle.projects.models import ProjectBudgetLine, Project
from bluebottle.projects.serializers import (
    ProjectBudgetLineSerializer,
    ProjectDocumentSerializer,
    ProjectPayoutSerializer
)
from bluebottle.projects.permissions import IsProjectOwner
from bluebottle.projects.serializers import (
    ProjectBudgetLineSerializer, ProjectDocumentSerializer,
    ProjectMediaSerializer,
    ProjectSupportSerializer)
from bluebottle.utils.utils import get_client_ip

from .models import ProjectDocument, ProjectBudgetLine, Project


class BudgetLinePagination(BluebottlePagination):
    page_size = 50


class ManageProjectBudgetLineList(generics.ListCreateAPIView):
    queryset = ProjectBudgetLine.objects.all()
    serializer_class = ProjectBudgetLineSerializer
    pagination_class = BudgetLinePagination
    permission_classes = (IsProjectOwner,)


class ManageProjectBudgetLineDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProjectBudgetLine.objects.all()
    serializer_class = ProjectBudgetLineSerializer
    permission_classes = (IsProjectOwner,)


class DocumentPagination(BluebottlePagination):
    page_size = 20


class ManageProjectDocumentList(generics.ListCreateAPIView):
    queryset = ProjectDocument.objects.all()
    serializer_class = ProjectDocumentSerializer
    pagination_class = DocumentPagination

    filter = ('project',)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, ip_address=get_client_ip(self.request))


class ManageProjectDocumentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProjectDocument.objects.all()
    serializer_class = ProjectDocumentSerializer
    pagination_class = DocumentPagination

    filter = ('project',)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user, ip_address=get_client_ip(self.request))


class ProjectMediaDetail(generics.RetrieveAPIView):
    queryset = Project.objects.all()
    pagination_class = BluebottlePagination
    serializer_class = ProjectMediaSerializer

    lookup_field = 'slug'


class ProjectSupportDetail(generics.RetrieveAPIView):
    queryset = Project.objects.all()
    pagination_class = BluebottlePagination
    serializer_class = ProjectSupportSerializer

    lookup_field = 'slug'
