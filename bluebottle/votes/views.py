from rest_framework import generics, exceptions

from bluebottle.projects.models import Project
from bluebottle.votes.models import Vote
from bluebottle.votes.serializers import VoteSerializer


class ProjectVoteList(generics.ListCreateAPIView):
    model = Vote
    paginate_by = 10
    serializer_class = VoteSerializer

    def get_queryset(self):
        """ Filter on project id"""
        project_id = self.kwargs['project_id']

        return super(ProjectVoteList, self).get_queryset().filter(project_id=project_id)

    def pre_save(self, obj):
        """
        Set the project and the voter.

        Check that a user has not vote before
        """
        project_id = self.kwargs['project_id']
        obj.project = Project.objects.get(id=project_id)
        try:
            self.get_queryset().get(voter=self.request.user)
            raise exceptions.ParseError('You cannot vote twice')
        except Vote.DoesNotExist:
            pass

        obj.voter = self.request.user
