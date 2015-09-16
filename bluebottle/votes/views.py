from rest_framework import generics, exceptions, filters, permissions

from bluebottle.utils.utils import get_client_ip
from bluebottle.projects.models import Project
from bluebottle.votes.models import Vote
from bluebottle.votes.serializers import VoteSerializer


class VoteList(generics.ListCreateAPIView):
    """ Retrieve votes. Or cast a vote as a user.
    Voting cannot happen twice.
    The list can be filtered adding vote=<id of user> and project=<slug of project>
    """
    model = Vote
    paginate_by = 10
    serializer_class = VoteSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('voter', 'project')

    def get_queryset(self):
        queryset = super(VoteList, self).get_queryset()
        project_slug = self.request.QUERY_PARAMS.get('project', None)
        if project_slug:
            project = Project.objects.get(slug=project_slug)
            queryset = queryset.filter(project=project)
        return queryset

    def pre_save(self, obj):
        """
        Set the voter.
        Check that a user has not vote before
        """

        try:
            self.get_queryset().get(voter=self.request.user,
                                    project=obj.project)
            raise exceptions.ParseError('You cannot vote twice')
        except Vote.DoesNotExist:
            pass

        obj.voter = self.request.user
        obj.ip_address = get_client_ip(self.request)
