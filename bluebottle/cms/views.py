from datetime import datetime, time
from pytz import timezone

from django.conf import settings
from rest_framework import generics

from bluebottle.cms.models import ResultPage
from bluebottle.cms.serializers import ResultPageSerializer


class ResultPageDetail(generics.RetrieveAPIView):
    queryset = ResultPage.objects.all()
    serializer_class = ResultPageSerializer

    def get_serializer_context(self):
        context = super(ResultPageDetail, self).get_serializer_context()
        obj = self.get_object()
        tz = timezone(settings.TIME_ZONE)

        context['start_date'] = tz.localize(
            datetime(*obj.start_date.timetuple()[:3])
        )
        context['end_date'] = tz.localize(
            datetime.combine(
                datetime(*obj.end_date.timetuple()[:3]),
                time.max,
            )
        )
        return context
