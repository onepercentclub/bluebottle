import json

from django.core.exceptions import ObjectDoesNotExist
from django.http.response import Http404
from fluent_contents.models import ContentItem

from bluebottle.clients import properties
from bluebottle.cms.models import HomePage
from bluebottle.cms.page_utils import BLOCK_RESOURCE_TYPES, create_page_block, resolve_page
from bluebottle.cms.permissions import (
    PageBlockPermission, PageEditorPermission, PlatformPagePermission, PageListPermission
)
from bluebottle.cms.serializers import (
    BLOCK_WRITE_SERIALIZERS,
    HomeSerializer, PageSerializer, PageListSerializer, BlockSerializer,
    NewsItemSerializer, PlatformPageSerializer
)
from bluebottle.news.models import NewsItem
from bluebottle.pages.models import Page, PlatformPage
from bluebottle.utils.permissions import TenantConditionalOpenClose, ResourcePermission
from bluebottle.utils.utils import get_language_from_request
from rest_framework import generics, status
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response

from bluebottle.utils.views import (
    ListAPIView, RetrieveAPIView, RetrieveUpdateAPIView, RetrieveUpdateDestroyAPIView,
    JsonApiViewMixin
)


class HomeDetail(JsonApiViewMixin, RetrieveAPIView):
    queryset = HomePage.objects.all()
    serializer_class = HomeSerializer

    permission_classes = [TenantConditionalOpenClose, ResourcePermission]


class BlockDetail(JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    queryset = ContentItem.objects.all()
    serializer_class = BlockSerializer

    permission_classes = [TenantConditionalOpenClose, PageBlockPermission]

    def get_serializer(self, *args, **kwargs):
        if kwargs.get('data') is not None and self.request.method in ('PATCH', 'PUT'):
            instance = args[0] if args else self.get_object()
            write_serializer = BLOCK_WRITE_SERIALIZERS.get(instance.__class__.__name__)
            if write_serializer:
                return write_serializer(*args, **kwargs)
        return BlockSerializer(*args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            BlockSerializer(instance, context=self.get_serializer_context()).data
        )


class PageBlockCreate(JsonApiViewMixin, generics.GenericAPIView):
    queryset = Page.objects.all()
    serializer_class = BlockSerializer
    permission_classes = [TenantConditionalOpenClose, PageEditorPermission]

    def post(self, request, slug):
        if not request.user.is_authenticated:
            raise NotAuthenticated()
        self.check_permissions(request)
        page = resolve_page(slug, request)
        try:
            document = json.loads(request.body.decode('utf-8'))
        except (TypeError, ValueError, UnicodeDecodeError):
            return Response(
                {'errors': [{'detail': 'Invalid JSON document', 'status': '400'}]},
                status=status.HTTP_400_BAD_REQUEST
            )

        resource_type = document.get('data', {}).get('type')
        if resource_type not in BLOCK_RESOURCE_TYPES:
            return Response(
                {'errors': [{'detail': 'Unsupported block type', 'status': '400'}]},
                status=status.HTTP_400_BAD_REQUEST
            )

        model_class = BLOCK_RESOURCE_TYPES[resource_type]
        write_serializer_class = BLOCK_WRITE_SERIALIZERS[model_class.__name__]
        serializer = write_serializer_class(data=document)
        serializer.is_valid(raise_exception=True)

        instance = create_page_block(
            page,
            resource_type,
            serializer.validated_data,
            write_serializer_class
        )
        attributes = document.get('data', {}).get('attributes') or {}
        for field, value in attributes.items():
            if field == 'image' or not hasattr(instance, field):
                continue
            setattr(instance, field, value)
        if attributes:
            instance.save()

        model_class = BLOCK_RESOURCE_TYPES[resource_type]
        instance = model_class.objects.get(pk=instance.pk)
        return Response(
            BlockSerializer(instance, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED
        )


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


class PageDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    serializer_class = PageSerializer
    queryset = Page.objects
    lookup_field = 'slug'
    permission_classes = [TenantConditionalOpenClose, PageEditorPermission]

    def get_queryset(self):
        if (
            self.request.user.is_authenticated and
            self.request.user.has_perm('pages.api_change_page')
        ):
            return Page.objects.all()
        return Page.objects.published()

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
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


class PageList(JsonApiViewMixin, ListAPIView):
    serializer_class = PageListSerializer
    permission_classes = [TenantConditionalOpenClose, PageListPermission]

    def get_queryset(self):
        language = get_language_from_request(self.request)
        return Page.objects.filter(
            language=language
        ).order_by('-modification_date', '-id')


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
