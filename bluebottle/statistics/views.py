from bluebottle.statistics.models import BaseStatistic, DatabaseStatistic
from bluebottle.statistics.renderers import StatisticsRenderer
from bluebottle.statistics.serializers import StatisticSerializer, OldStatisticSerializer, UserStatisticSerializer
from bluebottle.utils.permissions import TenantConditionalOpenClose
from bluebottle.utils.views import ListAPIView, JsonApiViewMixin


class OldStatisticList(JsonApiViewMixin, ListAPIView):
    serializer_class = OldStatisticSerializer
    permission_classes = [TenantConditionalOpenClose, ]
    queryset = BaseStatistic.objects.filter(active=True)

    renderer_classes = (StatisticsRenderer, )


class StatisticList(JsonApiViewMixin, ListAPIView):
    serializer_class = StatisticSerializer
    permission_classes = [TenantConditionalOpenClose, ]
    queryset = BaseStatistic.objects.filter(active=True)

    renderer_classes = (StatisticsRenderer, )


class UserStatisticList(JsonApiViewMixin, ListAPIView):
    serializer_class = UserStatisticSerializer
    permission_classes = [TenantConditionalOpenClose, ]
    renderer_classes = (StatisticsRenderer, )

    def get_queryset(self, *args, **kwargs):
        return [
            DatabaseStatistic(pk='my1', query='donated_total', name='Donated total', sequence=1),
            DatabaseStatistic(pk='my2', query='time_spent', name='Hours spent', sequence=2),
            DatabaseStatistic(pk='my3', query='deeds_done', name='Deeds done', sequence=3),
            DatabaseStatistic(pk='my4', query='collect_done', name='Collect done', sequence=3),
        ]
