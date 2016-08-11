from bluebottle.projects.views import ProjectMediaDetail
from ..views import (
    ManageProjectBudgetLineDetail, ManageProjectBudgetLineList,
    ManageProjectDocumentList, ManageProjectDocumentDetail)
from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',

    url(r'^(?P<slug>[\w-]+)/media/$',
        ProjectMediaDetail.as_view(),
        name='project-media-list'),

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
)
