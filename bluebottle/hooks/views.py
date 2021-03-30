from django.http import Http404

from bluebottle.activities.models import Activity
from bluebottle.hooks.models import SignalLog
from bluebottle.hooks.serializers import ActivityWebHookSerializer, ContributorWebHookSerializer
from bluebottle.utils.views import JsonApiViewMixin, RetrieveAPIView, ListAPIView


class LatestSignal(JsonApiViewMixin, RetrieveAPIView):
    queryset = SignalLog.objects.order_by('-created')
    permission_classes = []
    serializer_class = ActivityWebHookSerializer

    def get_serializer(self, instance, *args, **kwargs):
        if isinstance(instance.instance, Activity):
            serializer_class = ActivityWebHookSerializer
        else:
            serializer_class = ContributorWebHookSerializer

        kwargs['context'] = self.get_serializer_context()

        return serializer_class(instance=instance, *args, **kwargs)

    def get_object(self, queryset=None):
        obj = self.get_queryset().first()

        if not obj:
            raise Http404

        return obj


class SignalDetail(JsonApiViewMixin, RetrieveAPIView):
    queryset = SignalLog.objects.order_by('-created')
    permission_classes = []
    serializer_class = ActivityWebHookSerializer

    def get_serializer(self, instance, *args, **kwargs):
        if isinstance(instance.instance, Activity):
            serializer_class = ActivityWebHookSerializer
        else:
            serializer_class = ContributorWebHookSerializer

        kwargs['context'] = self.get_serializer_context()

        return serializer_class(instance=instance, *args, **kwargs)


class SignalList(JsonApiViewMixin, ListAPIView):
    queryset = SignalLog.objects.order_by('-created')
    permission_classes = []
    serializer_class = ContributorWebHookSerializer

    def get_queryset(self, *args, **kwargs):
        last = self.request.query_params.get('last', 0)
        return super(SignalList, self).get_queryset(*args, **kwargs).filter(id__gt=last)
