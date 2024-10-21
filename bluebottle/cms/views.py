from django.core.exceptions import ObjectDoesNotExist
from django.http.response import Http404
from fluent_contents.models import ContentItem

from bluebottle.clients import properties
from bluebottle.cms.models import HomePage
from bluebottle.cms.serializers import (
    HomeSerializer, PageSerializer, BlockSerializer
)
from bluebottle.pages.models import Page
from bluebottle.utils.permissions import TenantConditionalOpenClose, ResourcePermission
from bluebottle.utils.utils import get_language_from_request
from bluebottle.utils.views import RetrieveAPIView, JsonApiViewMixin


class HomeDetail(JsonApiViewMixin, RetrieveAPIView):
    queryset = HomePage.objects.all()
    serializer_class = HomeSerializer

    permission_classes = [TenantConditionalOpenClose, ResourcePermission]


class BlockDetail(JsonApiViewMixin, RetrieveAPIView):
    queryset = ContentItem.objects.all()
    serializer_class = BlockSerializer

    permission_classes = [TenantConditionalOpenClose, ResourcePermission]


class PageDetail(JsonApiViewMixin, RetrieveAPIView):
    serializer_class = PageSerializer

    queryset = Page.objects
    lookup_field = 'slug'

    def get_object(self, queryset=None):
        queryset = self.get_queryset().published()
        language = get_language_from_request(self.request)
        try:
            return queryset.get(
                language=language,
                slug=self.kwargs['slug']
            )
        except ObjectDoesNotExist:
            try:
                return queryset.get(
                    language=properties.LANGUAGE_CODE,
                    slug=self.kwargs['slug']
                )
            except ObjectDoesNotExist:
                raise Http404
