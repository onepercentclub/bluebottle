from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from bluebottle.projects.serializers import (
    ProjectBudgetLineSerializer, ProjectDocumentSerializer,
    ProjectMediaSerializer,
    ProjectSupportSerializer, ProjectWallpostPhotoSerializer)
from bluebottle.utils.utils import get_client_ip
from bluebottle.utils.views import (
    RetrieveAPIView, ListCreateAPIView, UpdateAPIView,
    RetrieveUpdateDestroyAPIView, PrivateFileView
)
from bluebottle.utils.permissions import OwnerPermission, OwnerOrAdminPermission
from bluebottle.wallposts.models import MediaWallpostPhoto
from .models import ProjectDocument, ProjectBudgetLine, Project
from .permissions import RelatedProjectOwnerPermission


class BudgetLinePagination(BluebottlePagination):
    page_size = 50


class ManageProjectBudgetLineList(ListCreateAPIView):
    queryset = ProjectBudgetLine.objects.all()
    serializer_class = ProjectBudgetLineSerializer
    pagination_class = BudgetLinePagination
    permission_classes = (RelatedProjectOwnerPermission,)


class ManageProjectBudgetLineDetail(RetrieveUpdateDestroyAPIView):
    queryset = ProjectBudgetLine.objects.all()
    serializer_class = ProjectBudgetLineSerializer
    permission_classes = (OwnerPermission,)


class DocumentPagination(BluebottlePagination):
    page_size = 20


class ManageProjectDocumentList(ListCreateAPIView):
    queryset = ProjectDocument.objects.all()
    serializer_class = ProjectDocumentSerializer
    pagination_class = DocumentPagination
    permission_classes = (RelatedProjectOwnerPermission,)

    filter = ('project',)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, ip_address=get_client_ip(self.request))


class ManageProjectDocumentDetail(RetrieveUpdateDestroyAPIView):
    queryset = ProjectDocument.objects.all()
    serializer_class = ProjectDocumentSerializer
    pagination_class = DocumentPagination
    permission_classes = (OwnerOrAdminPermission,)

    filter = ('project',)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user, ip_address=get_client_ip(self.request))


class ProjectDocumentFileView(PrivateFileView):
    queryset = ProjectDocument.objects
    field = 'file'
    permission_classes = (OwnerOrAdminPermission,)


class ProjectMediaDetail(RetrieveAPIView):
    queryset = Project.objects.all()
    pagination_class = BluebottlePagination
    serializer_class = ProjectMediaSerializer
    lookup_field = 'slug'


class ProjectMediaPhotoDetail(UpdateAPIView):
    queryset = MediaWallpostPhoto.objects.all()
    pagination_class = BluebottlePagination
    serializer_class = ProjectWallpostPhotoSerializer
    permission_classes = (OwnerPermission,)


class ProjectSupportDetail(RetrieveAPIView):
    queryset = Project.objects.all()
    pagination_class = BluebottlePagination
    serializer_class = ProjectSupportSerializer
    lookup_field = 'slug'
