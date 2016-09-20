from rest_framework import generics, permissions

from bluebottle.projects.models import Project
from bluebottle.surveys.models import Survey
from bluebottle.surveys.serializers import ProjectSurveySerializer


class ProjectSurveyList(generics.ListAPIView):
    """ Retrieve votes. Or cast a vote as a user.
    Voting cannot happen twice.
    The list can be filtered adding vote=<id of user> and project=<slug of project>
    """
    queryset = Survey.objects.all()
    serializer_class = ProjectSurveySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_serializer_context(self):
        context = super(ProjectSurveyList, self).get_serializer_context()
        context['project'] = Project.objects.get(slug=self.kwargs['slug'])
        return context
