from django.conf.urls import url

from bluebottle.time_based.views import (
    SkillList, SkillDetail
)

urlpatterns = [
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

]
