from datetime import datetime, time
from pytz import timezone

from django.conf import settings

from bluebottle.cms.models import ResultPage, HomePage
from bluebottle.cms.serializers import ResultPageSerializer, HomePageSerializer

from bluebottle.utils.views import RetrieveAPIView


class ResultPageDetail(RetrieveAPIView):
    queryset = ResultPage.objects.all()
    serializer_class = ResultPageSerializer

    def get_serializer_context(self):
        context = super(ResultPageDetail, self).get_serializer_context()
        obj = self.get_object()
        tz = timezone(settings.TIME_ZONE)

        if 'start_date' in context:
            context['start_date'] = tz.localize(
                datetime(*obj.start_date.timetuple()[:3])
            )

        if 'end_date' in context:
            context['end_date'] = tz.localize(
                datetime.combine(
                    datetime(*obj.end_date.timetuple()[:3]),
                    time.max,
                )
            )
        return context


class HomePageDetail(RetrieveAPIView):
    queryset = HomePage.objects.all()
    serializer_class = HomePageSerializer
