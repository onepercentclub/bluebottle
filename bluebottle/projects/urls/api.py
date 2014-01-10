from django.conf.urls import patterns, url

from ..views import (
    ManageProjectBudgetLineDetail, ManageProjectBudgetLineList,
    ManageProjectDetail, ManageProjectList, ProjectDetail,
    ProjectDetailFieldList, ProjectList, ProjectThemeDetail, ProjectThemeList,
    ProjectPreviewDetail, ProjectPreviewList)


urlpatterns = patterns(
    '',
    url(r'^projects/$', ProjectList.as_view(), name='project_list'),
    url(r'^projects/(?P<slug>[\w-]+)$', ProjectDetail.as_view(),
        name='project_detail'),

    url(r'^previews/$', ProjectPreviewList.as_view(),
        name='project_preview_list'),
    url(r'^previews/(?P<slug>[\w-]+)$', ProjectPreviewDetail.as_view(),
        name='project_preview_detail'),

    url(r'^themes/$', ProjectThemeList.as_view(), name='project_theme_list'),
    url(r'^themes/(?P<pk>\d+)$', ProjectThemeDetail.as_view(),
        name='project_theme_detail'),

    url(r'^fields/$', ProjectDetailFieldList.as_view(),
        name='project_detail_field_list'),

    # Manage stuff
    url(r'^manage/$', ManageProjectList.as_view(), name='project_manage_list'),
    url(r'^manage/(?P<slug>[\w-]+)$', ManageProjectDetail.as_view(),
        name='project_manage_detail'),

    url(r'^budgetlines/manage/$', ManageProjectBudgetLineList.as_view(),
        name='project_budgetline_manage_list'),
    url(r'^budgetlines/manage/(?P<pk>\d+)$', ManageProjectBudgetLineDetail.as_view(),
        name='project_budgetline_manage_detail'),
)
