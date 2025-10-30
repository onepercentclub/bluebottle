from django.core.exceptions import ObjectDoesNotExist
from django.http.response import Http404
from fluent_contents.models import ContentItem

from bluebottle.clients import properties
from bluebottle.cms.models import HomePage
from bluebottle.cms.permissions import PlatformPagePermission
from bluebottle.cms.serializers import (
    HomeSerializer, PageSerializer, BlockSerializer, NewsItemSerializer, PlatformPageSerializer
)
from bluebottle.news.models import NewsItem
from bluebottle.pages.models import Page, PlatformPage
from bluebottle.utils.permissions import TenantConditionalOpenClose, ResourcePermission
from bluebottle.utils.utils import get_language_from_request
from bluebottle.utils.views import ListAPIView, RetrieveAPIView, JsonApiViewMixin


class HomeDetail(JsonApiViewMixin, RetrieveAPIView):
    queryset = HomePage.objects.all()
    serializer_class = HomeSerializer

    permission_classes = [TenantConditionalOpenClose, ResourcePermission]


class BlockDetail(JsonApiViewMixin, RetrieveAPIView):
    queryset = ContentItem.objects.all()
    serializer_class = BlockSerializer

    permission_classes = [TenantConditionalOpenClose, ResourcePermission]


class CMSDetailView(JsonApiViewMixin, RetrieveAPIView):
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
                page = queryset.filter(slug=self.kwargs['slug']).first()
                if page:
                    return page
                raise Http404


class PageDetail(CMSDetailView):
    serializer_class = PageSerializer

    queryset = Page.objects


class PlatformPageDetail(CMSDetailView):
    serializer_class = PlatformPageSerializer
    queryset = PlatformPage.objects

    permission_classes = [PlatformPagePermission]

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        try:
            return queryset.get(
                slug=self.kwargs['slug']
            )
        except ObjectDoesNotExist:
            try:
                return queryset.get(
                    slug=self.kwargs['slug']
                )
            except ObjectDoesNotExist:
                page = queryset.filter(slug=self.kwargs['slug']).first()
                if page:
                    return page
                raise Http404


class NewsItemDetail(CMSDetailView):
    queryset = NewsItem.objects
    serializer_class = NewsItemSerializer


class NewsItemList(JsonApiViewMixin, ListAPIView):
    def get_queryset(self, *args, **kwargs):
        language = get_language_from_request(self.request)
        return NewsItem.objects.filter(
            language=language
        ).published().order_by('-publication_date', '-id')

    serializer_class = NewsItemSerializer
