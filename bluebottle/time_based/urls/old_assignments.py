from django.urls import path

from bluebottle.time_based.views import (
    SkillList, SkillDetail
)

urlpatterns = [
    path(
        '/skills',
        SkillList.as_view(),
        name='assignment-skill-list'
    ),
    path(
        '/skills/<int:pk>',
        SkillDetail.as_view(),
        name='assignment-skill'
    ),

]
