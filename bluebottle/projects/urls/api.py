from django.conf.urls import url

from ..views import (
    ManageProjectBudgetLineDetail, ManageProjectBudgetLineList,
    ManageProjectDocumentList, ManageProjectDocumentDetail,
    ProjectMediaDetail, ProjectSupportDetail,
    ProjectMediaPhotoDetail,
)


urlpatterns = [

    url(r'^media/(?P<slug>[\w-]+)$',
        ProjectMediaDetail.as_view(),
        name='project-media-detail'),

    url(r'^media/photo/(?P<pk>\d+)$',
        ProjectMediaPhotoDetail.as_view(),
        name='project-media-photo-detail'),

    url(r'^support/(?P<slug>[\w-]+)$',
        ProjectSupportDetail.as_view(),
        name='project-supporters-detail'),

    url(r'^budgetlines/$',
        ManageProjectBudgetLineList.as_view(),
        name='project-budgetline-list'),
    url(r'^budgetlines/(?P<pk>\d+)$',
        ManageProjectBudgetLineDetail.as_view(),
        name='project-budgetline-detail'),

    url(r'^documents/manage/$',
        ManageProjectDocumentList.as_view(),
        name='manage-project-document-list'),
    url(r'^documents/manage/(?P<pk>\d+)$',
        ManageProjectDocumentDetail.as_view(),
        name='manage-project-document-detail'),
]
