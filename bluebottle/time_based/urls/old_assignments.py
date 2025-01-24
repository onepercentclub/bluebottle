from django.urls import re_path

from bluebottle.time_based.views import (
    SkillList, SkillDetail
)

urlpatterns = [
    re_path(
        r'^/skills$',
        SkillList.as_view(),
        name='assignment-skill-list'
    ),
    re_path(
        r'^/skills/(?P<pk>\d+)$',
        SkillDetail.as_view(),
        name='assignment-skill'
    ),

]
