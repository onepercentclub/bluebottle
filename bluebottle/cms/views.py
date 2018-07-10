from datetime import datetime, time
from pytz import timezone

from django.db.models import Q
from django.conf import settings
from django.utils.timezone import now

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
    queryset = Page.objects.all()
    serializer_class = PageSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return super(PageDetail, self).get_queryset().filter(
            Q(publication_end_date__gte=now()) | Q(publication_end_date__isnull=True),
            status=Page.PageStatus.published,
            publication_date__lte=now(),
            language=self.request.LANGUAGE_CODE
        )


class NewsItemDetail(RetrieveAPIView):
    queryset = NewsItem.objects.all().published()
    serializer_class = NewsItemSerializer
    lookup_field = 'slug'
