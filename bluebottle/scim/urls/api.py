from django.conf.urls import url
from bluebottle.scim.views import (
    ServiceProviderConfigView, SchemaListView, SchemaRetrieveView,
    ResourceTypeRetrieveView, ResourceTypeListView,
    UserListView, UserDetailView,
    GroupListView, GroupDetailView
)


urlpatterns = [
    url(
        r'^ServiceProviderConfig$',
        ServiceProviderConfigView.as_view(),
        name='scim-service-provider-config'
    ),
    url(
        r'^Schemas$',
        SchemaListView.as_view(),
        name='scim-schema-list'
    ),
    url(
        r'^Schemas/(?P<id>[\:\.\w-]+)$',
        SchemaRetrieveView.as_view(),
        name='scim-schema-detail'
    ),
    url(
        r'^ResourceTypes$',
        ResourceTypeListView.as_view(),
        name='scim-resource-type-list'
    ),
    url(
        r'^ResourceTypes/(?P<id>[\w]+)$',
        ResourceTypeRetrieveView.as_view(),
        name='scim-resource-type-detail'
    ),
    url(
        r'^Users$',
        UserListView.as_view(),
        name='scim-user-list'
    ),
    url(
        r'^Users/goodup-user-(?P<pk>[\w]+)$',
        UserDetailView.as_view(),
        name='scim-user-detail'
    ),
    url(
        r'^Groups$',
        GroupListView.as_view(),
        name='scim-group-list'
    ),
    url(
        r'^Groups/goodup-group-(?P<pk>[\w]+)$',
        GroupDetailView.as_view(),
        name='scim-group-detail'
    ),
]
