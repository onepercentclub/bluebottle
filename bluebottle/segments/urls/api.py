from django.conf.urls import url

from bluebottle.segments.views import SegmentList, SegmentTypeList


urlpatterns = [
    url(
        r'^types/$',
        SegmentTypeList.as_view(),
        name='segment-type-list'
    ),
    url(
        r'^segments/$',
        SegmentList.as_view(),
        name='segment-list'
    ),
]
