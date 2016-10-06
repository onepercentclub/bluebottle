from django.conf.urls import patterns, url

from bluebottle.surveys.views import SurveyUpdateView

urlpatterns = patterns(
    '',
    url(r'^update/(?P<survey_id>[\d]+)$',
        SurveyUpdateView.as_view(), name='survey-update'),
)
