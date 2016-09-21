from django.conf.urls import patterns, url

from bluebottle.surveys.views import ProjectSurveyList

urlpatterns = patterns(
    '',
    url(r'^$', ProjectSurveyList.as_view(), name='project_survey_list'),
)
