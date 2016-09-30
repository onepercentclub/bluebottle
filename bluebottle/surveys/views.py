from django.db import connection
from django.http.response import HttpResponse
from django.views.generic.base import View
from rest_framework import generics, permissions

from bluebottle.projects.models import Project
from bluebottle.surveys.models import Survey
from bluebottle.surveys.serializers import ProjectSurveySerializer
from bluebottle.surveys.tasks import sync_survey



class ProjectSurveyList(generics.ListAPIView):
    """
    Retrieve surveys for a project.
    """
    queryset = Survey.objects.all()
    serializer_class = ProjectSurveySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_serializer_context(self):
        context = super(ProjectSurveyList, self).get_serializer_context()
        context['project'] = Project.objects.get(slug=self.request.query_params['project'])
        return context


class SurveyUpdateView(View):

    def get(self, request, **kwargs):
        survey_id = kwargs['survey_id']
        try:
            survey = Survey.objects.get(remote_id=survey_id)
        except Survey.DoesNotExist:
            raise Exception("Couldn't find survey: {0}".format(survey_id))
        sync_survey.delay(connection.tenant, survey)
        return HttpResponse('success')
    
    post = get