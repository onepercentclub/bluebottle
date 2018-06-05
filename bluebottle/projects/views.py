import csv

from django.http.response import HttpResponse

from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from bluebottle.projects.serializers import (
    ProjectBudgetLineSerializer,
    ProjectMediaSerializer, ProjectImageSerializer,
    ProjectSupportSerializer, ProjectWallpostPhotoSerializer)
from bluebottle.utils.admin import prep_field
from bluebottle.utils.views import (
    RetrieveAPIView, ListCreateAPIView, CreateAPIView, OwnerListViewMixin,
    RetrieveUpdateDestroyAPIView, PrivateFileView, UpdateAPIView
)
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission, RelatedResourceOwnerPermission
)
from bluebottle.wallposts.models import MediaWallpostPhoto
from .models import ProjectDocument, ProjectBudgetLine, Project, ProjectImage


class BudgetLinePagination(BluebottlePagination):
    page_size = 50


class ManageProjectBudgetLineList(OwnerListViewMixin, ListCreateAPIView):
    queryset = ProjectBudgetLine.objects
    serializer_class = ProjectBudgetLineSerializer
    pagination_class = BudgetLinePagination
    permission_classes = (RelatedResourceOwnerPermission,)

    owner_filter_field = 'project__owner'

    def get_queryset(self):
        qs = super(ManageProjectBudgetLineList, self).get_queryset()

        if not self.request.user.has_perm('projects.api_read_budgetline'):
            qs.filter(project__owner=self.request.user)

        return qs


class ManageProjectBudgetLineDetail(RetrieveUpdateDestroyAPIView):
    queryset = ProjectBudgetLine.objects.all()
    serializer_class = ProjectBudgetLineSerializer
    permission_classes = (ResourceOwnerPermission,)


class ProjectDocumentFileView(PrivateFileView):
    queryset = ProjectDocument.objects
    field = 'file'
    permission_classes = (
        OneOf(ResourcePermission, RelatedResourceOwnerPermission),
    )


class ProjectSupportersExportView(PrivateFileView):
    fields = (
        ('order__user__email', 'Email'),
        ('order__user__full_name', 'Name'),
        ('created', 'Donation Date'),
        ('amount_currency', 'Currency'),
        ('amount', 'Amount'),
        ('reward__title', 'Reward'),
    )

    model = Project

    def get(self, request, *args, **kwargs):
        instance = self.get_object()

        response = HttpResponse()
        response['Content-Disposition'] = 'attachment; filename="supporters.csv"'
        response['Content-Type'] = 'text/csv'

        writer = csv.writer(response)

        writer.writerow([field[1] for field in self.fields])
        for donation in instance.donations.filter(order__order_type='one-off'):
            writer.writerow([
                prep_field(request, donation, field[0]) for field in self.fields
            ])

        return response


class ProjectMediaDetail(RetrieveAPIView):
    queryset = Project.objects.all()
    pagination_class = BluebottlePagination
    serializer_class = ProjectMediaSerializer
    lookup_field = 'slug'


class ProjectMediaPhotoDetail(UpdateAPIView):
    queryset = MediaWallpostPhoto.objects.all()
    pagination_class = BluebottlePagination
    serializer_class = ProjectWallpostPhotoSerializer
    permission_classes = (RelatedResourceOwnerPermission,)


class ProjectSupportDetail(RetrieveAPIView):
    queryset = Project.objects.all()
    pagination_class = BluebottlePagination
    serializer_class = ProjectSupportSerializer
    lookup_field = 'slug'


class ProjectImageCreate(CreateAPIView):
    permission_classes = (
        OneOf(ResourcePermission, RelatedResourceOwnerPermission),
    )

    queryset = ProjectImage.objects.all()
    serializer_class = ProjectImageSerializer
