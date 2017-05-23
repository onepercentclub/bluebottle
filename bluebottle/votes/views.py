from rest_framework import generics, filters, permissions

from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from bluebottle.utils.utils import get_client_ip
from bluebottle.projects.models import Project
from bluebottle.votes.models import Vote
from bluebottle.votes.serializers import VoteSerializer


class VoteList(generics.ListCreateAPIView):
    """ Retrieve votes. Or cast a vote as a user.
    Voting cannot happen twice.
    The list can be filtered adding vote=<id of user> and project=<slug of project>
    """
    queryset = Vote.objects.all()
    pagination_class = BluebottlePagination
    serializer_class = VoteSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('voter',)

    def get_queryset(self):
        queryset = super(VoteList, self).get_queryset()
        project_slug = self.request.query_params.get('project', None)
        if project_slug:
            project = Project.objects.get(slug=project_slug)
            queryset = queryset.filter(project=project)
        return queryset

    def perform_create(self, serializer):
        """
        Set the voter.
        Check that a user has not voted before
        """
        serializer.save(ip_address=get_client_ip(self.request))
