from django.utils.translation import get_language

from bluebottle.utils.views import JsonApiViewMixin, RetrieveAPIView
from bluebottle.voting.models import Poll
from bluebottle.voting.serializers import PollSerializer


class PollDetail(JsonApiViewMixin, RetrieveAPIView):
    queryset = Poll.objects.filter(status='open')
    serializer_class = PollSerializer

    def get_queryset(self):
        return self.queryset.translated(get_language()).prefetch_related(
            'options'
        )
