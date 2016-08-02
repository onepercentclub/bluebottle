from bluebottle.projects.views import (
    ManageProjectBudgetLineDetail, ManageProjectBudgetLineList,
    ManageProjectDocumentList, ManageProjectDocumentDetail,
    ProjectPayoutList, ProjectPayoutDetail
)
from django.conf.urls import patterns, url
from surlex.dj import surl

urlpatterns = patterns(
    '',

    url(r'^budgetlines/$',
       ManageProjectBudgetLineList.as_view(),
       name='project-budgetline-list'),

    surl(r'^budgetlines/<pk:#>$',
        ManageProjectBudgetLineDetail.as_view(),
        name='project-budgetline-detail'),

    url(r'^documents/manage/$',
       ManageProjectDocumentList.as_view(),
       name='manage-project-document-list'),

    surl(r'^documents/manage/<pk:#>$',
        ManageProjectDocumentDetail.as_view(),
        name='manage-project-document-detail'),

    url(r'^payouts/$',
        ProjectPayoutList.as_view(),
        name='project-payout-list'),
    url(r'^payouts/(?P<pk>[\d]+)$',
        ProjectPayoutDetail.as_view(),
        name='project-payout-detail'),
)
