from rest_framework.pagination import PageNumberPagination

from bluebottle.assignments.serializers import (
    SkillSerializer
)
from bluebottle.tasks.models import Skill
from bluebottle.utils.permissions import (
    TenantConditionalOpenClose
)
from bluebottle.utils.views import (
    JsonApiViewMixin, ListAPIView, TranslatedApiViewMixin, RetrieveAPIView
)


class SkillPagination(PageNumberPagination):
    page_size = 10000


class SkillList(TranslatedApiViewMixin, JsonApiViewMixin, ListAPIView):
    serializer_class = SkillSerializer
    queryset = Skill.objects.filter(disabled=False)
    permission_classes = [TenantConditionalOpenClose, ]
    pagination_class = SkillPagination

    def get_queryset(self):
        return super().get_queryset().order_by('translations__name')


class SkillDetail(TranslatedApiViewMixin, JsonApiViewMixin, RetrieveAPIView):
    serializer_class = SkillSerializer
    queryset = Skill.objects.filter(disabled=False)
    permission_classes = [TenantConditionalOpenClose, ]
