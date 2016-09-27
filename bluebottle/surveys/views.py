from rest_framework import generics, permissions

from bluebottle.projects.models import Project
from bluebottle.surveys.models import Survey
from bluebottle.surveys.serializers import ProjectSurveySerializer


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
