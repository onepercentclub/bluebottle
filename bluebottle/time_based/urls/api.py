from django.urls import include, re_path

from bluebottle.time_based.views import (
    TimeContributionDetail,
    SkillList,
    SkillDetail,
    SlotParticipantExportView, PeriodActivityDetailView
)

urlpatterns = [
    re_path(
        r'^/contributions/time/(?P<pk>\d+)$',
        TimeContributionDetail.as_view(),
        name='time-contribution-detail'
    ),

    re_path(
        r'^/slot/export/(?P<pk>[\d]+)$',
        SlotParticipantExportView.as_view(),
        name='slot-participant-export'
    ),

    re_path(
        r'^/skills$',
        SkillList.as_view(),
        name='skill-list'
    ),
    re_path(
        r'^/skills/(?P<pk>\d+)$',
        SkillDetail.as_view(),
        name='skill'
    ),

    re_path(
        r'^/period/(?P<pk>\d+)$',
        PeriodActivityDetailView.as_view(),
        name="period-detail",
    ),
    re_path(r"^/date", include("bluebottle.time_based.urls.date_api")),
    re_path(r"^/deadline", include("bluebottle.time_based.urls.deadline_api")),
    re_path(r"^/periodic", include("bluebottle.time_based.urls.periodic_api")),
    re_path(r"^/schedule", include("bluebottle.time_based.urls.schedule_api")),
    re_path(r"^/teams", include("bluebottle.time_based.urls.team_api")),
]
