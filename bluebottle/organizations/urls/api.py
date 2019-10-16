from django.conf.urls import url

from bluebottle.organizations.views import (
    OrganizationList, OrganizationDetail,
    OrganizationContactList, OrganizationContactDetail
)

urlpatterns = [
    url(r'^$', OrganizationList.as_view(), name='organization_list'),
    url(r'^/(?P<pk>\d+)$', OrganizationDetail.as_view(),
        name='organization_detail'),
    url(r'^/contacts/$', OrganizationContactList.as_view(),
        name='organization_contact_list'),
    url(r'^/contacts/(?P<pk>\d+)$', OrganizationContactDetail.as_view(),
        name='organization_contact_detail')
]
