from bluebottle.projects.views import ProjectDetailFieldList
from django.conf.urls import patterns, url, include
from surlex.dj import surl
from .views import (ProjectDetail, ProjectList, ManageProjectList, ManageProjectDetail, ProjectThemeList,
                    ProjectThemeDetail, ProjectPreviewList, ProjectPreviewDetail, ManageProjectBudgetLineList,
                    ManageProjectBudgetLineDetail)

urlpatterns = patterns('',

    url(r'^projects/$', ProjectList.as_view(), name='project-list'),
    surl(r'^projects/<slug:s>$', ProjectDetail.as_view(), name='project-detail'),

    url(r'^previews/$', ProjectPreviewList.as_view(), name='project-preview-list'),
    surl(r'^previews/<slug:s>$', ProjectPreviewDetail.as_view(), name='project-preview-detail'),

    surl(r'^themes/$', ProjectThemeList.as_view(), name='project-theme-list'),
    surl(r'^themes/<pk:#>$', ProjectThemeDetail.as_view(), name='project-theme-detail'),

    surl(r'^fields/$', ProjectDetailFieldList.as_view(), name='project-detail-field-list'),

    # Manage stuff
    url(r'^manage/$', ManageProjectList.as_view(), name='project-manage-list'),
    surl(r'^manage/<slug:s>$', ManageProjectDetail.as_view(), name='project-manage-detail'),

    url(r'^budgetlines/manage/$', ManageProjectBudgetLineList.as_view(), name='project-budgetline-manage-detail'),
    surl(r'^budgetlines/manage/<pk:#>$', ManageProjectBudgetLineDetail.as_view(), name='project-budgetline-manage-detail'),

)
