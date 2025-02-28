from django.urls import re_path
from bluebottle.scim.views import (
    ServiceProviderConfigView, SchemaListView, SchemaRetrieveView,
    ResourceTypeRetrieveView, ResourceTypeListView,
    UserListView, UserDetailView,
    GroupListView, GroupDetailView
)


urlpatterns = [
    re_path(
        r'^ServiceProviderConfig$',
        ServiceProviderConfigView.as_view(),
        name='scim-service-provider-config'
    ),
    re_path(
        r'^Schemas$',
        SchemaListView.as_view(),
        name='scim-schema-list'
    ),
    re_path(
        r'^Schemas/(?P<id>[\:\.\w-]+)$',
        SchemaRetrieveView.as_view(),
        name='scim-schema-detail'
    ),
    re_path(
        r'^ResourceTypes$',
        ResourceTypeListView.as_view(),
        name='scim-resource-type-list'
    ),
    re_path(
        r'^ResourceTypes/(?P<id>[\w]+)$',
        ResourceTypeRetrieveView.as_view(),
        name='scim-resource-type-detail'
    ),
    re_path(
        r'^Users$',
        UserListView.as_view(),
        name='scim-user-list'
    ),
    re_path(
        r'^Users/goodup-user-(?P<pk>[\w]+)$',
        UserDetailView.as_view(),
        name='scim-user-detail'
    ),
    re_path(
        r'^Groups$',
        GroupListView.as_view(),
        name='scim-group-list'
    ),
    re_path(
        r'^Groups/goodup-group-(?P<pk>[\w]+)$',
        GroupDetailView.as_view(),
        name='scim-group-detail'
    ),
]
