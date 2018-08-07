from django.conf.urls import url

from bluebottle.projects.views import (
    ManageProjectBudgetLineDetail, ManageProjectBudgetLineList,
    ProjectMediaDetail, ProjectSupportDetail,
    ProjectMediaPhotoDetail, ProjectImageCreate
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
    url(r'^project-images/$',
        ProjectImageCreate.as_view(),
        name='project-image-create'),
]
