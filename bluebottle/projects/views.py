from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from bluebottle.projects.serializers import ProjectImageSerializer
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, RelatedResourceOwnerPermission
)
from bluebottle.utils.views import (
    CreateAPIView
)
from .models import ProjectImage


class BudgetLinePagination(BluebottlePagination):
    page_size = 50


class ProjectImageCreate(CreateAPIView):
    permission_classes = (
        OneOf(ResourcePermission, RelatedResourceOwnerPermission),
    )

    queryset = ProjectImage.objects.all()
    serializer_class = ProjectImageSerializer
