import json

from rest_framework import generics, status
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response

from bluebottle.content.models import ContentBlock, ContentPage
from bluebottle.content.page_utils import (
    BLOCK_RESOURCE_TYPES,
    BLOCK_TYPE_TO_RESOURCE,
    create_content_block,
    resolve_page,
)
from bluebottle.content.permissions import (
    ContentBlockPermission,
    ContentPageEditorPermission,
    ContentPageListPermission,
)
from bluebottle.content.serializers import (
    BLOCK_WRITE_SERIALIZERS,
    ContentBlockPolymorphicSerializer,
    ContentPageListSerializer,
    ContentPageSerializer,
    ContentPageWriteSerializer,
    READ_SERIALIZERS,
    serialize_content_block,
)
from bluebottle.utils.permissions import TenantConditionalOpenClose
from bluebottle.utils.utils import get_language_from_request
from bluebottle.utils.views import (
    JsonApiViewMixin,
    ListCreateAPIView,
    RetrieveUpdateAPIView,
    RetrieveUpdateDestroyAPIView,
)


class ContentPageDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    serializer_class = ContentPageSerializer
    queryset = ContentPage.objects.all()
    lookup_field = 'slug'
    permission_classes = [TenantConditionalOpenClose, ContentPageEditorPermission]

    def get_serializer_class(self):
        if self.request.method in ('PATCH', 'PUT'):
            return ContentPageWriteSerializer
        return ContentPageSerializer

    def get_queryset(self):
        if (
            self.request.user.is_authenticated and
            self.request.user.has_perm('pages.api_change_page')
        ):
            return ContentPage.objects.all()
        return ContentPage.objects.published()

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        language = get_language_from_request(self.request)
        from django.core.exceptions import ObjectDoesNotExist
        from django.http import Http404
        from bluebottle.clients import properties

        try:
            return queryset.get(language=language, slug=self.kwargs['slug'])
        except ObjectDoesNotExist:
            try:
                return queryset.get(language=properties.LANGUAGE_CODE, slug=self.kwargs['slug'])
            except ObjectDoesNotExist:
                page = queryset.filter(slug=self.kwargs['slug']).first()
                if page:
                    return page
                raise Http404


class ContentPageList(JsonApiViewMixin, ListCreateAPIView):
    serializer_class = ContentPageListSerializer
    permission_classes = [TenantConditionalOpenClose, ContentPageListPermission]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ContentPageWriteSerializer
        return ContentPageListSerializer

    def perform_create(self, serializer):
        serializer.save(language=self._language_for_create())

    def _language_for_create(self):
        language = self.request.data.get('language')
        if language:
            return language
        return get_language_from_request(self.request)

    def get_queryset(self):
        language = get_language_from_request(self.request)
        return ContentPage.objects.filter(
            language=language
        ).order_by('-modification_date', '-id')


class ContentBlockDetail(JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    queryset = ContentBlock.objects.all()
    serializer_class = ContentBlockPolymorphicSerializer
    permission_classes = [TenantConditionalOpenClose, ContentBlockPermission]

    def get_serializer(self, *args, **kwargs):
        if kwargs.get('data') is not None and self.request.method in ('PATCH', 'PUT'):
            instance = args[0] if args else self.get_object()
            resource_type = BLOCK_TYPE_TO_RESOURCE.get(instance.block_type)
            write_serializer = BLOCK_WRITE_SERIALIZERS.get(resource_type)
            if write_serializer:
                return write_serializer(*args, **kwargs)
        return ContentBlockPolymorphicSerializer(*args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        representation = serialize_content_block(
            instance,
            context=self.get_serializer_context(),
        )
        self.resource_name = False
        return Response({'data': representation})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        representation = serialize_content_block(
            instance,
            context=self.get_serializer_context(),
        )
        self.resource_name = False
        return Response({'data': representation})


class ContentBlockCreate(JsonApiViewMixin, generics.GenericAPIView):
    queryset = ContentPage.objects.all()
    serializer_class = ContentBlockPolymorphicSerializer
    permission_classes = [TenantConditionalOpenClose, ContentPageEditorPermission]
    resource_name = False

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

        write_serializer_class = BLOCK_WRITE_SERIALIZERS[resource_type]
        serializer = write_serializer_class(data=document)
        serializer.is_valid(raise_exception=True)

        meta = document.get('data', {}).get('meta') or {}
        insert_after = meta.get('insert-after') or meta.get('insertAfter')
        insert_before = meta.get('insert-before') or meta.get('insertBefore')

        try:
            instance = create_content_block(
                page,
                resource_type,
                serializer.validated_data,
                write_serializer_class,
                insert_after=insert_after,
                insert_before=insert_before,
            )
        except ValueError as error:
            return Response(
                {'errors': [{'detail': str(error), 'status': '400'}]},
                status=status.HTTP_400_BAD_REQUEST
            )

        attributes = document.get('data', {}).get('attributes') or {}
        for field, value in attributes.items():
            if field == 'image' or not hasattr(instance, field):
                continue
            setattr(instance, field, value)
        if attributes:
            instance.save()

        representation = serialize_content_block(
            instance,
            context=self.get_serializer_context(),
        )
        return Response({'data': representation}, status=status.HTTP_201_CREATED)
