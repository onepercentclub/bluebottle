from django.conf.urls import url

from bluebottle.assignments.views import (
    AssignmentList, AssignmentDetail, ApplicantList, ApplicantDetail,
    AssignmentTransitionList)

urlpatterns = [
    # Assignments
    url(r'^$',
        AssignmentList.as_view(),
        name='assignment-list'),
    url(r'^(?P<slug>[\w-]+)$',
        AssignmentDetail.as_view(),
        name='assignment-detail'),
    url(r'^/transitions$',
        AssignmentTransitionList.as_view(),
        name='assignment-transition-list'),

    # Applicants
    url(r'^applicants/$',
        ApplicantList.as_view(),
        name='applicant-list'),
    url(r'^applicants/(?P<id>[\d]+)$',
        ApplicantDetail.as_view(),
        name='applicant-detail'),
]
