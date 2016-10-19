from django.conf.urls import url

from bluebottle.surveys.views import SurveyUpdateView

urlpatterns = [
    url(r'^update/(?P<survey_id>[\d]+)$',
        SurveyUpdateView.as_view(), name='survey-update'),
]
