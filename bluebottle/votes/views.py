from rest_framework import generics, exceptions
from django.http import Http404
from bluebottle.projects.models import Project
from bluebottle.votes.models import Vote
from bluebottle.votes.serializers import VoteSerializer


class ProjectVoteList(generics.ListCreateAPIView):
    """ Retrieve the votes belong to a project. Or cast a vote as a user.

    Voting cannot happen twice.

    The list can be filtered adding voter_id=<id of user>
    """
    model = Vote
    paginate_by = 10
    serializer_class = VoteSerializer

    def get_queryset(self):
        """ Filter on project id"""
        queryset = super(ProjectVoteList, self).get_queryset().filter(
            project_id=self.kwargs['project_id'])

        if 'voter_id' in self.request.QUERY_PARAMS:
            queryset = queryset.filter(voter_id=self.request.QUERY_PARAMS['voter_id'])

        return queryset

    def pre_save(self, obj):
        """
        Set the project and the voter.

        Check that a user has not vote before
        """
        if self.request.user.is_anonymous():
            raise exceptions.PermissionDenied()

        try:
            self.get_queryset().get(voter=self.request.user)
            raise exceptions.ParseError('You cannot vote twice')
        except Vote.DoesNotExist:
            pass

        try:
            project_id = self.kwargs['project_id']
            obj.project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            raise Http404('Project not found')

        obj.voter = self.request.user
