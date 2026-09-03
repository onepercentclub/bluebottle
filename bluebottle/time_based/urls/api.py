from django.urls import path
from django.urls import include, re_path

from bluebottle.time_based.views import (
    TimeContributionDetail,
    SkillList,
    SkillDetail,
    SlotParticipantExportView, PeriodActivityDetailView, RegistrationDocumentDetail, DateSlotTransitionList
)

urlpatterns = [
    path(
        '/contributions/time/<int:pk>',
        TimeContributionDetail.as_view(),
        name='time-contribution-detail'
    ),

    re_path(
        r'^/slot/export/(?P<pk>[\d]+)$',
        SlotParticipantExportView.as_view(),
        name='slot-participant-export'
    ),

    path(
        '/slot/transitions',
        DateSlotTransitionList.as_view(),
        name='slot-transition-list'
    ),

    path(
        '/skills',
        SkillList.as_view(),
        name='skill-list'
    ),
    path(
        '/skills/<int:pk>',
        SkillDetail.as_view(),
        name='skill'
    ),

    path(
        '/period/<int:pk>',
        PeriodActivityDetailView.as_view(),
        name="period-detail",
    ),

    path(
        '/registrations/<int:pk>/document',
        RegistrationDocumentDetail.as_view(),
        name='registration-document'
    ),

    path("/date", include("bluebottle.time_based.urls.date_api")),
    path("/deadline", include("bluebottle.time_based.urls.deadline_api")),
    path("/registered-date", include("bluebottle.time_based.urls.registered_date_api")),
    path("/periodic", include("bluebottle.time_based.urls.periodic_api")),
    path("/schedule", include("bluebottle.time_based.urls.schedule_api")),
    path("/teams", include("bluebottle.time_based.urls.team_api")),
]
