from datetime import datetime, time

from django.conf import settings
from pytz import timezone

from bluebottle.cms.models import ResultPage, HomePage
from bluebottle.cms.serializers import (
    ResultPageSerializer, HomePageSerializer, NewsItemSerializer,
    PageSerializer
)
from bluebottle.news.models import NewsItem
from bluebottle.pages.models import Page
from bluebottle.utils.views import RetrieveAPIView


class ResultPageDetail(RetrieveAPIView):
    queryset = ResultPage.objects.all()
    serializer_class = ResultPageSerializer

    def get_serializer_context(self):
        context = super(ResultPageDetail, self).get_serializer_context()
        obj = self.get_object()
        tz = timezone(settings.TIME_ZONE)

        if obj.start_date:
            context['start_date'] = tz.localize(
                datetime(*obj.start_date.timetuple()[:3])
            )

        if obj.end_date:
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


class PageDetail(RetrieveAPIView):
    queryset = Page.objects.published()
    serializer_class = PageSerializer
    lookup_field = 'slug'


class NewsItemDetail(RetrieveAPIView):
    queryset = NewsItem.objects.published()
    serializer_class = NewsItemSerializer
    lookup_field = 'slug'
