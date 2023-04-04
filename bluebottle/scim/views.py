from builtins import str
from builtins import object
from django.http import Http404

from django.contrib.auth.models import Group

from rest_framework import (
    generics, response, permissions, authentication, exceptions,
    renderers, parsers
)

from bluebottle.members.models import Member

from bluebottle.scim.models import SCIMPlatformSettings
from bluebottle.scim.serializers import SCIMMemberSerializer, SCIMGroupSerializer, SCIMPatchSerializer
from bluebottle.scim import scim_data
from bluebottle.scim.filters import SCIMFilter

from rest_framework import pagination

import logging
logger = logging.getLogger(__name__)


class SCIMPaginator(pagination.LimitOffsetPagination):
    default_limit = 1000
    limit_query_param = 'count'
    offset_query_param = 'startIndex'

    def get_paginated_response(self, data):
        return response.Response({
            'totalResults': self.count,
            'startIndex': self.offset + 1,
            'Resources': data,
            'itemsPerPage': self.limit,
            'schemas': ['urn:ietf:params:scim:api:messages:2.0:ListResponse'],
        })

    def get_offset(self, request):
        try:
            return pagination._positive_int(
                request.query_params[self.offset_query_param],
            ) - 1
        except (KeyError, ValueError):
            return 0


class SCIMUser(object):
    is_authenticated = True


class SCIMAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        token = SCIMPlatformSettings.objects.get().bearer_token
        if request.META.get('HTTP_AUTHORIZATION') == 'Bearer {}'.format(token):
            return (SCIMUser(), None)

    def authenticate_header(self, request):
        return 'Bearer'


class SCIMRenderer(renderers.JSONRenderer):
    media_type = 'application/scim+json'


class SCIMParser(parsers.JSONParser):
    media_type = 'application/scim+json'


class SCIMViewMixin(object):
    authentication_classes = (SCIMAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    pagination_class = SCIMPaginator
    renderer_classes = (SCIMRenderer, )
    parser_classes = (SCIMParser, parsers.JSONParser,)
    filter_backends = (SCIMFilter, )

    def handle_exception(self, exc):
        if isinstance(exc, Http404):
            status_code = 404
            data = {
                'schemas': ["urn:ietf:params:scim:api:messages:2.0:Error"],
                'status': status_code,
                'detail': 'The resource was not found'
            }
        else:
            try:
                codes = exc.get_codes()

                status_code = exc.status_code

                if isinstance(codes, dict):
                    if any(['unique' in error_codes for error_codes in codes.values()]):
                        error_code = 'uniqueness'
                        status_code = 409
                    else:
                        error_code = list(codes.values())[0]
                else:
                    error_code = codes

                data = {
                    'scimType': error_code,
                    'schemas': ["urn:ietf:params:scim:api:messages:2.0:Error"],
                    'status': status_code
                }

                if isinstance(exc.detail, dict):
                    data['details'] = '\n'.join(
                        '{}: {}'.format(key, ', '.join(value)) for key, value in list(exc.detail.items())
                    )
                else:
                    data['details'] = str(exc.detail)

            except AttributeError:
                raise exc

        return response.Response(data, status=status_code)

    def update(self, request, *args, **kwargs):
        logger.error(request.body)

        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        logger.error(request.body)

        instance = self.get_object()
        data = self.get_serializer(instance).data

        patch_serializer = SCIMPatchSerializer(data=request.data)

        serializer = self.get_serializer(instance, data=patch_serializer.patch(data), partial=True)
        serializer.is_valid(raise_exception=True)

        self.perform_update(serializer)

        return response.Response(serializer.data)


class StaticRetrieveAPIView(SCIMViewMixin, generics.RetrieveAPIView):
    def get(self, request, id):
        self.check_permissions(self.request)
        for item in self.data:
            if item['id'] == id:
                return response.Response(item)

        raise exceptions.NotFound('Resource not found: {}'.format(id))


class StaticListAPIView(SCIMViewMixin, generics.ListAPIView):
    def get(self, request):
        self.paginate_queryset(self.data)
        return self.get_paginated_response(self.data)


class ServiceProviderConfigView(StaticRetrieveAPIView):
    permission_classes = []
    data = scim_data.SERVICE_PROVIDER_CONFIG

    def get(self, request):
        self.check_permissions(self.request)
        return response.Response(self.data)


class SchemaListView(StaticListAPIView):
    data = scim_data.SCHEMAS


class SchemaRetrieveView(StaticRetrieveAPIView):
    data = scim_data.SCHEMAS


class ResourceTypeListView(StaticListAPIView):
    data = scim_data.RESOURCE_TYPES


class ResourceTypeRetrieveView(StaticRetrieveAPIView):
    data = scim_data.RESOURCE_TYPES


class UserListView(SCIMViewMixin, generics.ListCreateAPIView):
    queryset = Member.objects.filter(
        is_superuser=False, is_anonymized=False
    ).exclude(email='devteam+accounting@onepercentclub.com')

    serializer_class = SCIMMemberSerializer

    def perform_create(self, serializer):
        try:
            # If a user with the correct remote id but without an external id
            # exists, allow the create for once.
            # In this case the provisioning client does not know about the member, and
            # can continue as normal
            if 'remote_id' in serializer.validated_data:
                serializer.instance = Member.objects.get(
                    remote_id=serializer.validated_data['remote_id'],
                    scim_external_id__isnull=True
                )
        except Member.DoesNotExist:
            pass

        return super().perform_create(serializer)


class UserDetailView(SCIMViewMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Member.objects.filter(
        is_superuser=False, is_anonymized=False
    ).exclude(email='devteam+accounting@onepercentclub.com')

    serializer_class = SCIMMemberSerializer

    def perform_destroy(self, instance):
        instance.anonymize()


class GroupListView(SCIMViewMixin, generics.ListAPIView):
    queryset = Group.objects.exclude(name__in=('Anonymous', 'Authenticated', ))
    serializer_class = SCIMGroupSerializer


class GroupDetailView(SCIMViewMixin, generics.RetrieveUpdateAPIView):
    queryset = Group.objects.exclude(name__in=('Anonymous', 'Authenticated', ))
    serializer_class = SCIMGroupSerializer
