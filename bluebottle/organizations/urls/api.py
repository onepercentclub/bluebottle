from django.urls import path

from bluebottle.organizations.views import (
    OrganizationList, OrganizationDetail,
    OrganizationContactList, OrganizationContactDetail
)

urlpatterns = [
    path('', OrganizationList.as_view(), name='organization_list'),
    path(
        '/<int:pk>',
        OrganizationDetail.as_view(),
        name='organization_detail'
    ),
    path(
        '/contacts',
        OrganizationContactList.as_view(),
        name='organization_contact_list'
    ),
    path(
        '/contacts/<int:pk>',
        OrganizationContactDetail.as_view(),
        name='organization_contact_detail'
    )
]
