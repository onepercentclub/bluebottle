from django.conf.urls import patterns, url

from ..views import (
    ManageOrganizationList, ManageOrganizationDetail, OrganizationDetail, OrganizationList)

urlpatterns = patterns(
    '',
    url(r'^$', OrganizationList.as_view(), name='organization_list'),
    url(r'^(?P<pk>\d+)$', OrganizationDetail.as_view(), name='organization_detail'),
    url(r'^manage/$', ManageOrganizationList.as_view(), name='manage_organization_list'),
    url(r'^manage/(?P<pk>\d+)$', ManageOrganizationDetail.as_view(), name='manage_organization_detail'),
)
