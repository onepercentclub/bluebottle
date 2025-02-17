from django.conf.urls import include, url

from bluebottle.time_based.views import (
    TimeContributionDetail,
    SkillList,
    SkillDetail,
    SlotParticipantExportView, PeriodActivityDetailView
)

urlpatterns = [
    url(r'^/contributions/time/(?P<pk>\d+)$',
        TimeContributionDetail.as_view(),
        name='time-contribution-detail'),

    url(r'^/slot/export/(?P<pk>[\d]+)$',
        SlotParticipantExportView.as_view(),
        name='slot-participant-export'),

    url(
        r'^/skills$',
        SkillList.as_view(),
        name='skill-list'
    ),
    url(
        r'^/skills/(?P<pk>\d+)$',
        SkillDetail.as_view(),
        name='skill'
    ),

    url(
        r'^/period/(?P<pk>\d+)$',
        PeriodActivityDetailView.as_view(),
        name="period-detail",
    ),
    url(r"^/date", include("bluebottle.time_based.urls.date_api")),
    url(r"^/deadline", include("bluebottle.time_based.urls.deadline_api")),
    url(r"^/periodic", include("bluebottle.time_based.urls.periodic_api")),
    url(r"^/schedule", include("bluebottle.time_based.urls.schedule_api")),
    url(r"^/teams", include("bluebottle.time_based.urls.team_api")),
]
