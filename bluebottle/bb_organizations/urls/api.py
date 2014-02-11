from django.conf.urls import patterns, url

from ..views import (
    ManageOrganizationList, ManageOrganizationDetail, ManageOrganizationDocumentList,
    ManageOrganizationDocumentDetail, OrganizationDetail, OrganizationList)

urlpatterns = patterns(
    '',
    url(r'^$', OrganizationList.as_view(), name='organization_list'),
    url(r'^(?P<pk>\d+)$', OrganizationDetail.as_view(), name='organization_detail'),
    url(r'^manage/$', ManageOrganizationList.as_view(), name='manage_organization_list'),
    url(r'^manage/(?P<pk>\d+)$', ManageOrganizationDetail.as_view(), name='manage_organization_detail'),

    url(r'^documents/manage/$', ManageOrganizationDocumentList.as_view(), name='manage_organization_document_list'),
    url(r'^documents/manage/(?P<pk>\d+)$', ManageOrganizationDocumentDetail.as_view(),
        name='manage_organization_document_detail'),
)
