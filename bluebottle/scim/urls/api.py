from django.urls import path
from django.urls import re_path
from bluebottle.scim.views import (
    ServiceProviderConfigView, SchemaListView, SchemaRetrieveView,
    ResourceTypeRetrieveView, ResourceTypeListView,
    UserListView, UserDetailView,
    GroupListView, GroupDetailView
)


urlpatterns = [
    path(
        'ServiceProviderConfig',
        ServiceProviderConfigView.as_view(),
        name='scim-service-provider-config'
    ),
    path(
        'Schemas',
        SchemaListView.as_view(),
        name='scim-schema-list'
    ),
    re_path(
        r'^Schemas/(?P<id>[\:\.\w-]+)$',
        SchemaRetrieveView.as_view(),
        name='scim-schema-detail'
    ),
    path(
        'ResourceTypes',
        ResourceTypeListView.as_view(),
        name='scim-resource-type-list'
    ),
    re_path(
        r'^ResourceTypes/(?P<id>[\w]+)$',
        ResourceTypeRetrieveView.as_view(),
        name='scim-resource-type-detail'
    ),
    path(
        'Users',
        UserListView.as_view(),
        name='scim-user-list'
    ),
    re_path(
        r'^Users/goodup-user-(?P<pk>[\w]+)$',
        UserDetailView.as_view(),
        name='scim-user-detail'
    ),
    path(
        'Groups',
        GroupListView.as_view(),
        name='scim-group-list'
    ),
    re_path(
        r'^Groups/goodup-group-(?P<pk>[\w]+)$',
        GroupDetailView.as_view(),
        name='scim-group-detail'
    ),
]
