from django.conf.urls import url

from bluebottle.assignments.views import (
    AssignmentList, AssignmentDetail, ApplicantList, ApplicantDetail,
    AssignmentTransitionList, ApplicantTransitionList, ApplicantDocumentDetail,
    SkillList, SkillDetail
)

urlpatterns = [
    # Assignments
    url(r'^$',
        AssignmentList.as_view(),
        name='assignment-list'),
    url(r'^/(?P<pk>\d+)$',
        AssignmentDetail.as_view(),
        name='assignment-detail'),
    url(r'^/transitions$',
        AssignmentTransitionList.as_view(),
        name='assignment-transition-list'),

    # Applicants
    url(r'^/applicants$',
        ApplicantList.as_view(),
        name='applicant-list'),
    url(r'^/applicants/(?P<pk>\d+)$',
        ApplicantDetail.as_view(),
        name='applicant-detail'),
    url(r'^/applicants/transitions$',
        ApplicantTransitionList.as_view(),
        name='applicant-transition-list'),

    url(
        r'^/skills$',
        SkillList.as_view(),
        name='assignment-skill-list'
    ),
    url(
        r'^/skills/(?P<pk>\d+)$',
        SkillDetail.as_view(),
        name='assignment-skill'
    ),

    url(r'^/applicants/(?P<pk>\d+)/document$',
        ApplicantDocumentDetail.as_view(),
        name='applicant-document')
]
