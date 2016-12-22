import datetime
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
        context['start_date'] = datetime.datetime(
            *obj.start_date.timetuple()[:6], tzinfo=timezone(settings.TIME_ZONE)
        )
        context['end_date'] = datetime.datetime(
            *obj.end_date.timetuple()[:6], tzinfo=timezone(settings.TIME_ZONE)
        )
        return context
