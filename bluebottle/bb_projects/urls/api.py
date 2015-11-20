from django.conf.urls import patterns, url

from ..views import (
    ManageProjectDetail, ManageProjectList, ProjectDetail,
    ProjectList, ProjectThemeDetail, ProjectThemeList,
    ProjectPreviewDetail, ProjectPreviewList, ProjectTinyPreviewList,
    ProjectPhaseDetail, ProjectPhaseList, ProjectUsedThemeList,
    ProjectPhaseLogList, ProjectPhaseLogDetail,
    ManageProjectDocumentList, ManageProjectDocumentDetail)


urlpatterns = patterns(
    '',
    url(r'^projects/$', ProjectList.as_view(), name='project_list'),
    url(r'^projects/(?P<slug>[\w-]+)$', ProjectDetail.as_view(),
        name='project_detail'),

    url(r'^tiny-previews/$', ProjectTinyPreviewList.as_view(),
        name='project_tiny_preview_list'),
    url(r'^previews/$', ProjectPreviewList.as_view(),
        name='project_preview_list'),
    url(r'^previews/(?P<slug>[\w-]+)$', ProjectPreviewDetail.as_view(),
        name='project_preview_detail'),

    url(r'^phases/$', ProjectPhaseList.as_view(),
        name='project_phase_list'),
    url(r'^phases/(?P<pk>\d+)$', ProjectPhaseDetail.as_view(),
        name='project_phase'),

    url(r'^phases_log/$', ProjectPhaseLogList.as_view(),
        name='project_phase_log_list'),
    url(r'^phases_log/(?P<pk>\d+)$', ProjectPhaseLogDetail.as_view(),
        name='project_phase_log'),


    url(r'^themes/$', ProjectThemeList.as_view(), name='project_theme_list'),
    url(r'^used_themes/$', ProjectUsedThemeList.as_view(), name='project_used_theme_list'),
    url(r'^themes/(?P<pk>\d+)$', ProjectThemeDetail.as_view(),
        name='project_theme_detail'),

    # Manage stuff
    url(r'^manage/$', ManageProjectList.as_view(), name='project_manage_list'),
    url(r'^manage/(?P<slug>[\w-]+)$', ManageProjectDetail.as_view(), name='project_manage_detail'),

    url(r'^documents/manage/$', ManageProjectDocumentList.as_view(), name='manage_project_document_list'),
    url(r'^documents/manage/(?P<pk>\d+)$', ManageProjectDocumentDetail.as_view(),
        name='manage_project_document_detail'),

)
