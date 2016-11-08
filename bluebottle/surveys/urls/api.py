from django.conf.urls import url

from bluebottle.surveys.views import ProjectSurveyList

urlpatterns = [
    url(r'^$', ProjectSurveyList.as_view(), name='project_survey_list'),
]
