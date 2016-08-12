from bluebottle.projects.views import ProjectMediaDetail
from ..views import (
    ManageProjectBudgetLineDetail, ManageProjectBudgetLineList,
    ManageProjectDocumentList, ManageProjectDocumentDetail)
from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',

    url(r'^media/(?P<slug>[\w-]+)/$',
        ProjectMediaDetail.as_view(),
        name='project-media-detail'),

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
