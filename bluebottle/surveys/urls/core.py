from django.conf.urls import patterns, url

from bluebottle.surveys.views import ProjectSurveyList, SurveyUpdateView

urlpatterns = patterns(
    '',
    url(r'^update/(?P<survey_id>[\d]+)$',
        SurveyUpdateView.as_view(), name='survey-update'),
)
