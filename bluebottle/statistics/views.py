from bluebottle.statistics.renderers import StatisticsRenderer
from bluebottle.statistics.serializers import StatisticSerializer, OldStatisticSerializer
from bluebottle.statistics.models import BaseStatistic

from bluebottle.utils.views import ListAPIView, JsonApiViewMixin
from bluebottle.utils.permissions import TenantConditionalOpenClose


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
