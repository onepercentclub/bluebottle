from bluebottle.events.models import Event
from bluebottle.events.serializers import EventSerializer
from bluebottle.utils.views import ListAPIView, JsonApiViewMixin


class EventListView(JsonApiViewMixin, ListAPIView):
    model = Event
    paginate_by = 10
    serializer_class = EventSerializer
    queryset = Event.objects.all()
