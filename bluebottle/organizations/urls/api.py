from django.urls import re_path

from bluebottle.organizations.views import (
    OrganizationList, OrganizationDetail,
    OrganizationContactList, OrganizationContactDetail
)

urlpatterns = [
    re_path(r'^$', OrganizationList.as_view(), name='organization_list'),
    re_path(r'^/(?P<pk>\d+)$', OrganizationDetail.as_view(),
        name='organization_detail'),
    re_path(r'^/contacts$', OrganizationContactList.as_view(),
        name='organization_contact_list'),
    re_path(r'^/contacts/(?P<pk>\d+)$', OrganizationContactDetail.as_view(),
        name='organization_contact_detail')
]
